"""
Test Script for Multiple Images
================================
This script processes all images in test_images/ folder
and saves results to a CSV file for analysis.
"""

from skin_tone_detector import SkinToneDetector
from pathlib import Path
import csv
import sys


def test_all_images():
    """
    Process all images in test_images/ folder and save results.
    """
    print("="*60)
    print("BATCH TESTING - Skin Tone Detection")
    print("="*60)
    
    # Initialize detector once (more efficient)
    print("\nInitializing detector...")
    detector = SkinToneDetector()
    
    # Find all images
    test_dir = Path("test_images")
    if not test_dir.exists():
        print("ERROR: test_images/ directory not found!")
        return
    
    image_extensions = [".jpg", ".jpeg", ".png", ".bmp"]
    image_files = []
    for ext in image_extensions:
        image_files.extend(list(test_dir.glob(f"*{ext}")))
        image_files.extend(list(test_dir.glob(f"*{ext.upper()}")))
    
    if not image_files:
        print("ERROR: No images found in test_images/ directory!")
        return
    
    print(f"\nFound {len(image_files)} image(s) to process\n")
    
    # Process each image
    results = []
    successful = 0
    failed = 0
    
    for i, img_file in enumerate(image_files, 1):
        print(f"\n[{i}/{len(image_files)}] Processing: {img_file.name}")
        print("-" * 60)
        
        try:
            result, _, _ = detector.process_image(str(img_file))
            
            results.append({
                'image': img_file.name,
                'skin_tone': result['skin_tone'],
                'confidence': f"{result['confidence']:.2%}",
                'avg_brightness': f"{result.get('avg_v', 'N/A')}",
                'skin_pixels': result['num_skin_pixels'],
                'status': 'Success'
            })
            
            successful += 1
            print(f"[OK] Success: {result['skin_tone']} ({result['confidence']:.2%} confidence)")
            
        except Exception as e:
            results.append({
                'image': img_file.name,
                'skin_tone': 'N/A',
                'confidence': 'N/A',
                'avg_brightness': 'N/A',
                'skin_pixels': 'N/A',
                'status': f'Error: {str(e)}'
            })
            
            failed += 1
            print(f"[X] Failed: {str(e)}")
    
    # Save results to CSV
    output_file = "test_results.csv"
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['image', 'skin_tone', 'confidence', 'avg_brightness', 'skin_pixels', 'status']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Total images processed: {len(image_files)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"\nResults saved to: {output_file}")
    
    # Show distribution of skin tones
    if successful > 0:
        tones = [r['skin_tone'] for r in results if r['status'] == 'Success']
        print(f"\nSkin Tone Distribution:")
        print(f"  Light:   {tones.count('Light')}")
        print(f"  Medium:  {tones.count('Medium')}")
        print(f"  Dark:    {tones.count('Dark')}")
    
    print("="*60)


if __name__ == "__main__":
    try:
        test_all_images()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {str(e)}")
        sys.exit(1)
