import { Upload, Image as ImageIcon, X, Camera, Sparkles, CheckCircle2, AlertCircle } from 'lucide-react';
import { useState, useRef } from 'react';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

interface ImageUploadProps {
  onNavigate: (page: string) => void;
  onAnalysisComplete?: (analysis: any, recommendations: any, photoUrl?: string) => void;
}

const ANALYSIS_STEPS = [
  { label: 'Uploading Image', icon: Upload },
  { label: 'Detecting Face', icon: Camera },
  { label: 'Analyzing Skin Tone', icon: Sparkles },
  { label: 'Detecting Body Shape', icon: ImageIcon },
  { label: 'Generating Recommendations', icon: CheckCircle2 },
];

export default function ImageUpload({ onNavigate, onAnalysisComplete }: ImageUploadProps) {
  const [dragActive, setDragActive] = useState(false);
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [selectedImageFile, setSelectedImageFile] = useState<File | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [error, setError] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);
  const stepTimersRef = useRef<ReturnType<typeof setTimeout>[]>([]);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  const handleFile = (file: File) => {
    setError('');
    if (!file.type.startsWith('image/')) {
      setError('Please select an image file (JPG, PNG, WEBP)');
      return;
    }
    if (file.size > 16 * 1024 * 1024) {
      setError('Image must be smaller than 16MB');
      return;
    }
    setSelectedImageFile(file);
    const reader = new FileReader();
    reader.onload = (e) => {
      setSelectedImage(e.target?.result as string);
    };
    reader.readAsDataURL(file);
  };

  const simulateSteps = (totalTime: number) => {
    // Clear any previous timers
    stepTimersRef.current.forEach(clearTimeout);
    stepTimersRef.current = [];
    const stepTime = totalTime / ANALYSIS_STEPS.length;
    ANALYSIS_STEPS.forEach((_, i) => {
      const id = setTimeout(() => setCurrentStep(i), stepTime * i);
      stepTimersRef.current.push(id);
    });
  };

  const cancelStepTimers = () => {
    stepTimersRef.current.forEach(clearTimeout);
    stepTimersRef.current = [];
  };

  const handleAnalyze = async () => {
    if (!selectedImageFile) return;
    setIsAnalyzing(true);
    setCurrentStep(0);
    setError('');

    // Start step simulation (the actual API call may finish faster or slower)
    simulateSteps(8000);
    
    try {
      const token = localStorage.getItem('access_token');

      // Guard: require a valid token before even attempting the upload
      if (!token) {
        setIsAnalyzing(false);
        setCurrentStep(0);
        setError('You must be logged in to analyze a photo. Please log in and try again.');
        return;
      }

      // Step 1: Upload
      const formData = new FormData();
      formData.append('image', selectedImageFile);
      
      const uploadRes = await fetch(`${API_URL}/api/images/upload`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });
      
      if (!uploadRes.ok) {
        const errData = await uploadRes.json().catch(() => ({}));
        if (uploadRes.status === 401) {
          throw new Error('Your session has expired. Please log out and log in again.');
        }
        throw new Error(errData.error || 'Upload failed. Please try again.');
      }
      const uploadData = await uploadRes.json();
      const imageId = uploadData.image.id;
      
      setCurrentStep(2); // Jump to "Analyzing Skin Tone"

      // Step 2: ML Analysis
      const analyzeRes = await fetch(`${API_URL}/api/ml/analyze/${imageId}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (!analyzeRes.ok) {
        const errData = await analyzeRes.json().catch(() => ({}));
        const msg = errData.error || 'Analysis failed';
        const detail = errData.detail || '';
        // Provide user-friendly error messages
        if (analyzeRes.status === 422 || msg.toLowerCase().includes('no human')) {
          throw new Error('🚫 No person detected in this photo. Please upload a clear photo of yourself (full-body or portrait). Screenshots and non-human images cannot be analyzed.');
        }
        if (msg.includes('No face detected') || msg.includes('Insufficient skin')) {
          throw new Error('No person detected in the image. Please use a clear photo of yourself with your face and/or body visible.');
        }
        if (msg.includes('No pose landmarks')) {
          throw new Error('Could not detect body pose. Please use a full-body photo with good lighting.');
        }
        throw new Error(detail || msg);
      }
      
      const analyzeData = await analyzeRes.json();
      
      setCurrentStep(4); // "Generating Recommendations" complete
      
      // Short delay to show the final step before navigating
      await new Promise(resolve => setTimeout(resolve, 800));
      
      setIsAnalyzing(false);
      if (onAnalysisComplete) {
        onAnalysisComplete(analyzeData.analysis, analyzeData.recommendations, selectedImage || undefined);
      } else {
        onNavigate('analysis');
      }
    } catch (err: any) {
      console.error(err);
      cancelStepTimers();
      setError(err.message || 'An error occurred during analysis. Please try again.');
      setIsAnalyzing(false);
      setCurrentStep(0);
    }
  };

  const handleRemoveImage = () => {
    setSelectedImage(null);
    setSelectedImageFile(null);
    setError('');
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-rose-50 via-pink-50 to-orange-50 py-8 md:py-12 px-4">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-3xl md:text-5xl font-bold text-gray-900 mb-3" style={{ fontFamily: 'Outfit, sans-serif' }}>
            Upload Your Photo
          </h1>
          <p className="text-lg text-gray-600">
            Let our AI analyze your style and discover your fashion potential
          </p>
        </div>

        <div className="bg-white rounded-3xl shadow-xl p-6 md:p-10">
          {/* Error Banner */}
          {error && (
            <div className="mb-6 flex items-start gap-3 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl animate-fade-in-down">
              <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-medium text-sm">{error}</p>
              </div>
              <button onClick={() => setError('')} className="ml-auto flex-shrink-0">
                <X className="w-4 h-4" />
              </button>
            </div>
          )}

          {/* Analyzing State — Progress Steps */}
          {isAnalyzing ? (
            <div className="py-12 animate-fade-in">
              <div className="text-center mb-10">
                <div className="relative w-20 h-20 mx-auto mb-6">
                  <div className="w-20 h-20 rounded-full border-4 border-rose-200 border-t-rose-500 animate-spin" />
                  <Sparkles className="w-8 h-8 text-rose-500 absolute inset-0 m-auto" />
                </div>
                <h3 className="text-xl font-bold text-gray-900 mb-1">Analyzing Your Style</h3>
                <p className="text-sm text-gray-500">This usually takes 10-15 seconds</p>
              </div>

              <div className="max-w-md mx-auto space-y-3">
                {ANALYSIS_STEPS.map((step, index) => {
                  const Icon = step.icon;
                  const isActive = currentStep === index;
                  const isDone = currentStep > index;

                  return (
                    <div
                      key={index}
                      className={`flex items-center gap-3 p-3 rounded-xl transition-all duration-500 ${
                        isActive ? 'bg-rose-50 border border-rose-200 shadow-sm' :
                        isDone ? 'bg-green-50 border border-green-200' :
                        'bg-gray-50 border border-transparent opacity-50'
                      }`}
                    >
                      <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 transition-all ${
                        isDone ? 'bg-green-500' :
                        isActive ? 'bg-rose-500 animate-pulse' :
                        'bg-gray-300'
                      }`}>
                        {isDone ? (
                          <CheckCircle2 className="w-4 h-4 text-white" />
                        ) : (
                          <Icon className="w-4 h-4 text-white" />
                        )}
                      </div>
                      <span className={`text-sm font-medium ${
                        isDone ? 'text-green-700' :
                        isActive ? 'text-rose-700' :
                        'text-gray-400'
                      }`}>
                        {step.label}
                        {isActive && <span className="ml-1 animate-pulse">...</span>}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          ) : !selectedImage ? (
            /* Drop Zone */
            <div
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              className={`border-2 border-dashed rounded-2xl p-10 md:p-14 text-center transition-all cursor-pointer ${
                dragActive
                  ? 'border-rose-400 bg-rose-50 scale-[1.01]'
                  : 'border-gray-300 hover:border-rose-300 bg-gray-50/50'
              }`}
              onClick={() => fileInputRef.current?.click()}
            >
              <div className="flex flex-col items-center">
                <div className={`p-5 rounded-full mb-5 transition-all ${
                  dragActive ? 'bg-rose-200 scale-110' : 'bg-gradient-to-br from-rose-100 to-pink-100'
                }`}>
                  <Upload className="w-10 h-10 text-rose-500" />
                </div>

                <h3 className="text-xl font-bold text-gray-900 mb-2">
                  {dragActive ? 'Drop your image here!' : 'Drag & drop your photo'}
                </h3>

                <p className="text-gray-500 mb-5">or click to browse files</p>

                <label className="cursor-pointer" onClick={(e) => e.stopPropagation()}>
                  <span className="bg-gradient-to-r from-rose-500 to-pink-500 text-white px-8 py-3 rounded-full font-semibold hover:shadow-lg hover:shadow-rose-200 transition-all inline-block hover:scale-105 active:scale-95">
                    Browse Files
                  </span>
                  <input
                    ref={fileInputRef}
                    type="file"
                    className="hidden"
                    accept="image/*"
                    onChange={handleChange}
                  />
                </label>

                <p className="text-xs text-gray-400 mt-5">
                  Supported: JPG, PNG, WEBP • Max 16MB
                </p>
              </div>
            </div>
          ) : (
            /* Image Preview + Analyze */
            <div className="space-y-6 animate-scale-in">
              <div className="relative rounded-2xl overflow-hidden bg-gray-100">
                <img
                  src={selectedImage}
                  alt="Your uploaded photo"
                  className="w-full h-auto max-h-[28rem] object-contain mx-auto"
                />
                <button
                  onClick={handleRemoveImage}
                  className="absolute top-3 right-3 bg-white/90 backdrop-blur p-2 rounded-full shadow-lg hover:bg-white hover:scale-110 transition-all"
                >
                  <X className="w-5 h-5 text-gray-700" />
                </button>
              </div>

              <div className="bg-gradient-to-r from-rose-50 to-pink-50 p-5 rounded-xl border border-rose-100">
                <div className="flex items-start space-x-3">
                  <ImageIcon className="w-5 h-5 text-rose-500 flex-shrink-0 mt-0.5" />
                  <div>
                    <h4 className="font-semibold text-gray-900 text-sm mb-1">Tips for best results</h4>
                    <ul className="text-xs text-gray-600 space-y-1">
                      <li>• Use a full-body photo for body shape detection</li>
                      <li>• Ensure your face is clearly visible for skin tone analysis</li>
                      <li>• Good lighting improves accuracy significantly</li>
                    </ul>
                  </div>
                </div>
              </div>

              <div className="flex flex-col sm:flex-row gap-3">
                <button
                  onClick={handleAnalyze}
                  className="flex-1 bg-gradient-to-r from-rose-500 to-pink-500 text-white px-8 py-4 rounded-full font-semibold hover:shadow-xl hover:shadow-rose-200 transition-all hover:scale-[1.02] active:scale-[0.98] flex items-center justify-center gap-2"
                >
                  <Sparkles className="w-5 h-5" />
                  Analyze My Style
                </button>
                <button
                  onClick={handleRemoveImage}
                  className="sm:flex-initial bg-white text-gray-700 px-6 py-4 rounded-full font-medium border-2 border-gray-200 hover:border-rose-300 transition-all"
                >
                  Different Photo
                </button>
              </div>
            </div>
          )}
        </div>

        <div className="mt-6 text-center">
          <p className="text-xs text-gray-500">
            🔒 Your privacy matters. Photos are processed securely and used only for analysis.
          </p>
        </div>
      </div>
    </div>
  );
}
