# StyleAura Backend API

Flask-based backend API for StyleAura AI Fashion Advisor with MongoDB database.

## Features

- **User Authentication**: Secure signup/login with JWT tokens
- **Image Upload**: Secure file handling with validation
- **AI Analysis Storage**: Store skin tone, body shape, and style analysis results
- **Recommendations**: Personalized outfit and style recommendations
- **User Profiles**: Complete user management and history tracking
- **RESTful APIs**: Clean, well-documented endpoints with proper error handling

## Quick Start

### Prerequisites

- Python 3.8+
- MongoDB 4.4+
- pip

### Installation

1. **Clone and navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your MongoDB credentials and secrets
   ```

5. **Set up MongoDB database:**
   ```bash
   # Your MongoDB Atlas cluster is already configured
   # The connection string is set in the configuration
   # No local MongoDB setup needed
   ```

6. **Update MONGO_URI in .env (if needed):**
   ```
   MONGO_URI=mongodb+srv://styleaura:styleaura@cluster0.uqxkaub.mongodb.net/?appName=Cluster0
   ```

7. **Run the application:**
   ```bash
   python app.py
   ```

The API will be available at `http://localhost:5000`

## API Endpoints

### Authentication
- `POST /api/auth/signup` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/refresh` - Refresh JWT token
- `GET /api/auth/me` - Get current user info
- `PUT /api/auth/update-profile` - Update user profile

### Images
- `POST /api/images/upload` - Upload image
- `GET /api/images/` - Get user images (paginated)
- `GET /api/images/{id}` - Get image details
- `GET /api/images/{id}/file` - Serve image file
- `DELETE /api/images/{id}` - Delete image

### Analysis
- `POST /api/analysis/create` - Create analysis record
- `GET /api/analysis/` - Get user analyses (paginated)
- `GET /api/analysis/{id}` - Get specific analysis
- `PUT /api/analysis/{id}` - Update analysis
- `DELETE /api/analysis/{id}` - Delete analysis
- `GET /api/analysis/image/{image_id}` - Get analysis by image

### Recommendations
- `POST /api/recommendations/create` - Create single recommendation
- `POST /api/recommendations/batch` - Create multiple recommendations
- `GET /api/recommendations/` - Get user recommendations (filtered)
- `GET /api/recommendations/{id}` - Get specific recommendation
- `GET /api/recommendations/analysis/{analysis_id}` - Get recommendations by analysis
- `PUT /api/recommendations/{id}` - Update recommendation
- `DELETE /api/recommendations/{id}` - Delete recommendation

### Users
- `GET /api/users/profile` - Get user profile with statistics
- `GET /api/users/history` - Get user activity history
- `GET /api/users/dashboard` - Get user dashboard data
- `DELETE /api/users/delete-account` - Delete user account

### Health Check
- `GET /api/health` - API health check

## Database Schema

### Users Collection
```json
{
  "_id": ObjectId,
  "email": "user@example.com",
  "password_hash": "bcrypt_hash",
  "first_name": "John",
  "last_name": "Doe",
  "created_at": ISODate,
  "updated_at": ISODate
}
```

### User Images Collection
```json
{
  "_id": ObjectId,
  "user_id": ObjectId,
  "filename": "unique_filename.jpg",
  "original_filename": "user_photo.jpg",
  "file_path": "/uploads/unique_filename.jpg",
  "file_size": 1024000,
  "mime_type": "image/jpeg",
  "uploaded_at": ISODate
}
```

### Analysis Collection
```json
{
  "_id": ObjectId,
  "user_id": ObjectId,
  "image_id": ObjectId,
  "skin_tone": "Warm",
  "body_shape": "Hourglass",
  "style_personality": "Classic Elegant",
  "confidence_score": 0.95,
  "color_palette": ["Rose Pink", "Warm Beige"],
  "face_shape": "Oval",
  "height_estimate": 170.5,
  "body_measurements": {},
  "created_at": ISODate
}
```

### Recommendations Collection
```json
{
  "_id": ObjectId,
  "user_id": ObjectId,
  "analysis_id": ObjectId,
  "category": "outfit",
  "title": "Recommended Outfit",
  "description": "Style description",
  "recommendation_type": "clothing",
  "tags": ["casual", "summer"],
  "priority": 1,
  "seasonal_relevance": "all",
  "created_at": ISODate
}
```

## Security Features

- JWT-based authentication with refresh tokens
- Password hashing with bcrypt
- File upload validation (type, size, MIME)
- Input validation and sanitization
- CORS configuration for frontend integration

## Error Handling

All endpoints return consistent error responses:
```json
{
  "error": "Error message description"
}
```

Common HTTP status codes:
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `404` - Not Found
- `409` - Conflict
- `500` - Internal Server Error

## File Upload Configuration

- **Allowed formats**: PNG, JPG, JPEG, WEBP
- **Max file size**: 10MB per image
- **Storage**: Local filesystem (configurable to cloud storage)
- **Security**: Filename sanitization and unique ID generation

## AI Model Integration

The backend is designed to easily integrate ML models:

1. **Image Analysis**: Models can output analysis data directly to `/api/analysis/create`
2. **Recommendations**: Use `/api/recommendations/batch` for bulk recommendations
3. **Modular Design**: Add new model endpoints without modifying existing code

## Development

### Running Tests
```bash
# Add test files and run
python -m pytest tests/
```

### Database Management
MongoDB Atlas provides cloud-hosted database management:
```bash
# Connect to MongoDB Atlas (use MongoDB Compass or mongosh)
mongosh "mongodb+srv://styleaura:styleaura@cluster0.uqxkaub.mongodb.net/?appName=Cluster0"

# View collections
show collections

# Query users
db.users.find().pretty()

# Create indexes for performance
db.users.createIndex({email: 1}, {unique: true})
```

## Production Deployment

1. **Environment Variables**: Set all secrets in production
2. **Database**: MongoDB Atlas cluster is pre-configured and ready to use
3. **File Storage**: Consider AWS S3 or similar for image storage
4. **Web Server**: Use Gunicorn or uWSGI behind Nginx
5. **SSL**: Enable HTTPS for all API endpoints
6. **Rate Limiting**: Implement rate limiting for API protection

## License

This project is part of StyleAura AI Fashion Advisor.
