#!/usr/bin/env python3
"""
AI Learning Tutor - API Testing Script
Tests all major endpoints with sample data
"""

import asyncio
import json
import requests
import time
from pprint import pprint

BASE_URL = "http://localhost:8080"

def test_health():
    """Test health endpoints"""
    print("\n🔍 Testing health endpoints...")
    
    response = requests.get(f"{BASE_URL}/")
    print("Root endpoint:", response.json())
    
    response = requests.get(f"{BASE_URL}/api/health/ai")
    print("AI services health:", response.json())

def test_user_creation():
    """Test user profile creation"""
    print("\n👤 Testing user creation...")
    
    user_data = {
        "username": "test_student",
        "learning_style": "visual",
        "difficulty_preference": "intermediate",
        "subjects_of_interest": ["Python Programming", "Data Science"]
    }
    
    response = requests.post(f"{BASE_URL}/api/users/create", json=user_data)
    if response.status_code == 200:
        user_id = response.json()["user_id"]
        print("✅ User created:", user_id)
        return user_id
    else:
        print("❌ User creation failed:", response.text)
        return None

def test_courses():
    """Test course listing"""
    print("\n📚 Testing course endpoints...")
    
    response = requests.get(f"{BASE_URL}/api/courses")
    if response.status_code == 200:
        courses = response.json()["courses"]
        print(f"✅ Found {len(courses)} courses")
        for course in courses:
            print(f"  - {course['subject']}: {course['total_modules']} modules")
        return courses[0] if courses else None
    else:
        print("❌ Course listing failed:", response.text)
        return None

def test_personalized_content(user_id):
    """Test personalized content retrieval"""
    print("\n📖 Testing personalized content...")
    
    content_request = {
        "user_id": user_id,
        "topic": "python programming",
        "learning_style": "visual"
    }
    
    response = requests.post(f"{BASE_URL}/api/content/personalized", json=content_request)
    if response.status_code == 200:
        content = response.json()
        print("✅ Personalized content retrieved")
        print(f"  - Recommended difficulty: {content['recommended_difficulty']}")
        print(f"  - Content items: {len(content['content'])}")
        return True
    else:
        print("❌ Content retrieval failed:", response.text)
        return False

def test_quiz_generation(user_id):
    """Test quiz generation"""
    print("\n🧠 Testing quiz generation...")
    
    quiz_request = {
        "user_id": user_id,
        "module_id": "python-intro",
        "difficulty_level": 2,
        "question_count": 3
    }
    
    response = requests.post(f"{BASE_URL}/api/quiz/generate", json=quiz_request)
    if response.status_code == 200:
        quiz = response.json()
        print("✅ Quiz generated")
        print(f"  - Questions: {len(quiz['questions'])}")
        print(f"  - Estimated time: {quiz['estimated_time']} seconds")
        return quiz
    else:
        print("❌ Quiz generation failed:", response.text)
        return None

def test_quiz_submission(user_id, quiz_id="python-intro"):
    """Test quiz submission"""
    print("\n📝 Testing quiz submission...")
    
    submission = {
        "user_id": user_id,
        "module_id": quiz_id,
        "answers": [
            {
                "question_id": "q1",
                "selected_option": 1,
                "time_taken": 15.5,
                "confidence_level": 0.8
            },
            {
                "question_id": "q2", 
                "selected_option": 0,
                "time_taken": 12.3,
                "confidence_level": 0.9
            }
        ],
        "total_time": 30.0
    }
    
    response = requests.post(f"{BASE_URL}/api/quiz/submit", json=submission)
    if response.status_code == 200:
        results = response.json()
        print("✅ Quiz submitted")
        print(f"  - Score: {results['percentage']:.1f}%")
        print(f"  - Next review: {results['next_review']['next_review_date']}")
        return results
    else:
        print("❌ Quiz submission failed:", response.text)
        return None

def test_analytics(user_id):
    """Test analytics endpoint"""
    print("\n📊 Testing analytics...")
    
    response = requests.get(f"{BASE_URL}/api/analytics/{user_id}")
    if response.status_code == 200:
        analytics = response.json()
        print("✅ Analytics retrieved")
        print("Overall stats:")
        pprint(analytics["overall_stats"])
        return analytics
    else:
        print("❌ Analytics failed:", response.text)
        return None

def main():
    """Run all tests"""
    print("🧪 AI Learning Tutor API Tests")
    print("=" * 50)
    
    # Test health
    test_health()
    
    # Test user creation
    user_id = test_user_creation()
    if not user_id:
        print("❌ Cannot continue without user ID")
        return
    
    # Test courses
    courses = test_courses()
    
    # Test personalized content
    test_personalized_content(user_id)
    
    # Test quiz generation
    quiz = test_quiz_generation(user_id)
    
    # Test quiz submission
    test_quiz_submission(user_id)
    
    # Test analytics
    test_analytics(user_id)
    
    print("\n✅ All tests completed!")
    print(f"👤 Test user ID: {user_id}")
    print("🌐 API Documentation: http://localhost:8080/docs")

if __name__ == "__main__":
    main()
