#!/usr/bin/env python3
"""
Backend Testing Suite for Luxura Distribution
Tests backend APIs AND Playwright backlink automation system
"""

import requests
import json
import sys
import asyncio
import os
from datetime import datetime
from pathlib import Path

# Add backend to path for backlink automation testing
sys.path.append('/app/backend')

# Base URL for the API
BASE_URL = "https://hair-extensions-shop.preview.emergentagent.com/api"

class LuxuraAPITester:
    def __init__(self):
        self.session = requests.Session()
        self.results = []
        self.total_tests = 0
        self.passed_tests = 0
        
    def log_result(self, test_name, success, message, response_data=None):
        """Log test result"""
        self.total_tests += 1
        if success:
            self.passed_tests += 1
            
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        
        if response_data:
            result["response_sample"] = response_data
            
        self.results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        
    def test_health_check(self):
        """Test GET /api/ - Health check"""
        try:
            response = self.session.get(f"{BASE_URL}/")
            
            if response.status_code == 200:
                data = response.json()
                if "message" in data and "status" in data:
                    self.log_result("Health Check", True, f"API healthy: {data.get('message')}", data)
                else:
                    self.log_result("Health Check", False, "Response missing required fields", data)
            else:
                self.log_result("Health Check", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Health Check", False, f"Exception: {str(e)}")
    
    def test_products_list(self):
        """Test GET /api/products - Should return products array"""
        try:
            response = self.session.get(f"{BASE_URL}/products")
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    # Check first product structure
                    first_product = data[0]
                    required_fields = ["id", "name", "price", "description", "category", "images", "in_stock"]
                    missing_fields = [field for field in required_fields if field not in first_product]
                    
                    if not missing_fields:
                        self.log_result("Products List", True, f"Found {len(data)} products with correct structure", {
                            "count": len(data),
                            "sample_product": first_product
                        })
                    else:
                        self.log_result("Products List", False, f"Missing fields in product: {missing_fields}", first_product)
                else:
                    self.log_result("Products List", False, f"Expected array of products, got: {type(data)}", data)
            else:
                self.log_result("Products List", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Products List", False, f"Exception: {str(e)}")
    
    def test_single_product(self):
        """Test GET /api/products/{id} - Get single product"""
        product_id = "genius-noir-1"
        try:
            response = self.session.get(f"{BASE_URL}/products/{product_id}")
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["id", "name", "price", "description", "category", "images", "in_stock"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields and data.get("id") == product_id:
                    self.log_result("Single Product", True, f"Product {product_id} retrieved successfully", data)
                else:
                    issues = []
                    if missing_fields:
                        issues.append(f"Missing fields: {missing_fields}")
                    if data.get("id") != product_id:
                        issues.append(f"Wrong product ID returned: {data.get('id')}")
                    self.log_result("Single Product", False, "; ".join(issues), data)
            else:
                self.log_result("Single Product", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Single Product", False, f"Exception: {str(e)}")
    
    def test_products_filter(self):
        """Test GET /api/products?category=genius-weft - Filter by category"""
        try:
            response = self.session.get(f"{BASE_URL}/products", params={"category": "genius-weft"})
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    # Check that all products belong to the genius-weft category
                    wrong_category = [p for p in data if p.get("category") != "genius-weft"]
                    
                    if not wrong_category:
                        self.log_result("Products Filter", True, f"Found {len(data)} genius-weft products", {
                            "count": len(data),
                            "category_filter": "genius-weft"
                        })
                    else:
                        self.log_result("Products Filter", False, f"Found {len(wrong_category)} products with wrong category", {
                            "wrong_products": wrong_category[:2]
                        })
                else:
                    self.log_result("Products Filter", False, f"Expected array of products, got: {type(data)}", data)
            else:
                self.log_result("Products Filter", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Products Filter", False, f"Exception: {str(e)}")
    
    def test_categories(self):
        """Test GET /api/categories - Should return 4 categories"""
        try:
            response = self.session.get(f"{BASE_URL}/categories")
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    if len(data) == 4:
                        # Check category structure
                        first_category = data[0] if data else {}
                        required_fields = ["id", "name", "description"]
                        missing_fields = [field for field in required_fields if field not in first_category]
                        
                        if not missing_fields:
                            self.log_result("Categories", True, f"Found {len(data)} categories with correct structure", {
                                "count": len(data),
                                "categories": [cat.get("name") for cat in data]
                            })
                        else:
                            self.log_result("Categories", False, f"Missing fields in category: {missing_fields}", first_category)
                    else:
                        self.log_result("Categories", False, f"Expected 4 categories, got {len(data)}", {
                            "count": len(data),
                            "categories": [cat.get("name") for cat in data]
                        })
                else:
                    self.log_result("Categories", False, f"Expected array of categories, got: {type(data)}", data)
            else:
                self.log_result("Categories", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Categories", False, f"Exception: {str(e)}")
    
    def test_blog_list(self):
        """Test GET /api/blog - Should return blog posts"""
        try:
            response = self.session.get(f"{BASE_URL}/blog")
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    first_post = data[0]
                    required_fields = ["id", "title", "content", "excerpt", "author", "created_at"]
                    missing_fields = [field for field in required_fields if field not in first_post]
                    
                    if not missing_fields:
                        self.log_result("Blog List", True, f"Found {len(data)} blog posts with correct structure", {
                            "count": len(data),
                            "sample_post": {
                                "id": first_post.get("id"),
                                "title": first_post.get("title"),
                                "author": first_post.get("author")
                            }
                        })
                    else:
                        self.log_result("Blog List", False, f"Missing fields in blog post: {missing_fields}", first_post)
                else:
                    self.log_result("Blog List", False, f"Expected array of blog posts, got: {type(data)}", data)
            else:
                self.log_result("Blog List", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Blog List", False, f"Exception: {str(e)}")
    
    def test_single_blog_post(self):
        """Test GET /api/blog/{id} - Get single post"""
        post_id = "entretien-extensions"
        try:
            response = self.session.get(f"{BASE_URL}/blog/{post_id}")
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["id", "title", "content", "excerpt", "author", "created_at"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields and data.get("id") == post_id:
                    self.log_result("Single Blog Post", True, f"Blog post {post_id} retrieved successfully", {
                        "id": data.get("id"),
                        "title": data.get("title"),
                        "author": data.get("author")
                    })
                else:
                    issues = []
                    if missing_fields:
                        issues.append(f"Missing fields: {missing_fields}")
                    if data.get("id") != post_id:
                        issues.append(f"Wrong post ID returned: {data.get('id')}")
                    self.log_result("Single Blog Post", False, "; ".join(issues), data)
            else:
                self.log_result("Single Blog Post", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Single Blog Post", False, f"Exception: {str(e)}")
    
    def test_salons(self):
        """Test GET /api/salons - Should return salon list"""
        try:
            response = self.session.get(f"{BASE_URL}/salons")
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    first_salon = data[0]
                    required_fields = ["id", "name", "address", "city"]
                    missing_fields = [field for field in required_fields if field not in first_salon]
                    
                    if not missing_fields:
                        self.log_result("Salons List", True, f"Found {len(data)} salons with correct structure", {
                            "count": len(data),
                            "sample_salon": {
                                "name": first_salon.get("name"),
                                "city": first_salon.get("city")
                            }
                        })
                    else:
                        self.log_result("Salons List", False, f"Missing fields in salon: {missing_fields}", first_salon)
                else:
                    self.log_result("Salons List", False, f"Expected array of salons, got: {type(data)}", data)
            else:
                self.log_result("Salons List", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Salons List", False, f"Exception: {str(e)}")
    
    def test_cart_unauthorized(self):
        """Test cart endpoints without authentication - should return 401"""
        endpoints = [
            ("GET /api/cart", "get"),
            ("POST /api/cart", "post")
        ]
        
        for endpoint_name, method in endpoints:
            try:
                if method == "get":
                    response = self.session.get(f"{BASE_URL}/cart")
                else:  # POST
                    response = self.session.post(f"{BASE_URL}/cart", json={"product_id": "test", "quantity": 1})
                
                if response.status_code == 401:
                    self.log_result(f"Cart Auth - {endpoint_name}", True, "Correctly returned 401 Unauthorized", {
                        "status_code": response.status_code,
                        "response": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                    })
                else:
                    self.log_result(f"Cart Auth - {endpoint_name}", False, f"Expected 401, got {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_result(f"Cart Auth - {endpoint_name}", False, f"Exception: {str(e)}")
    
    def test_auth_endpoints(self):
        """Test authentication-related endpoints"""
        # Test /auth/me without auth - should return 401
        try:
            response = self.session.get(f"{BASE_URL}/auth/me")
            if response.status_code == 401:
                self.log_result("Auth Me - Unauthorized", True, "Correctly returned 401 for /auth/me without auth")
            else:
                self.log_result("Auth Me - Unauthorized", False, f"Expected 401, got {response.status_code}")
        except Exception as e:
            self.log_result("Auth Me - Unauthorized", False, f"Exception: {str(e)}")
        
        # Test /auth/session endpoint exists (but can't test fully without real session)
        try:
            response = self.session.post(f"{BASE_URL}/auth/session", json={"session_id": "test_invalid"})
            # We expect this to fail with 401 or 400, but the endpoint should exist
            if response.status_code in [400, 401]:
                self.log_result("Auth Session - Endpoint Exists", True, f"Auth session endpoint exists (returned {response.status_code})")
            else:
                self.log_result("Auth Session - Endpoint Exists", False, f"Unexpected response: {response.status_code}")
        except Exception as e:
            self.log_result("Auth Session - Endpoint Exists", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all backend tests"""
        print("=" * 80)
        print("🧪 LUXURA DISTRIBUTION BACKEND API TESTS")
        print("=" * 80)
        
        # Core public endpoints
        self.test_health_check()
        self.test_products_list()
        self.test_single_product()
        self.test_products_filter()
        self.test_categories()
        self.test_blog_list()
        self.test_single_blog_post()
        self.test_salons()
        
        # Authentication tests
        self.test_cart_unauthorized()
        self.test_auth_endpoints()
        
    def test_backlink_automation_system(self):
        """Test the Playwright backlink automation system"""
        print("\n🔗 TESTING BACKLINK AUTOMATION SYSTEM")
        print("-" * 40)
        
        # Test 1: Import backlink automation module
        try:
            from backlink_automation import (
                LUXURA_BUSINESS, 
                DIRECTORIES, 
                run_backlink_automation,
                get_business_info,
                get_directories_list
            )
            self.log_result("Backlink Module Import", True, "Successfully imported backlink automation module")
            
            # Test business info
            business_info = get_business_info()
            if business_info.get("company_name") == "Luxura Distribution":
                self.log_result("Business Info Validation", True, "Business info correctly configured")
            else:
                self.log_result("Business Info Validation", False, "Business info missing or incorrect")
            
            # Test directories list
            directories = get_directories_list()
            if len(directories) >= 5:
                self.log_result("Directories List", True, f"Found {len(directories)} target directories")
                
                # Check for required directories from review request
                required_dirs = ["Hotfrog Canada", "Cylex Canada", "iGlobal.co", "Canpages", "Yelp Canada"]
                found_dirs = [d.get("name", "") for d in directories]
                missing_dirs = [d for d in required_dirs if d not in found_dirs]
                
                if not missing_dirs:
                    self.log_result("Required Directories", True, "All required directories are configured")
                else:
                    self.log_result("Required Directories", False, f"Missing directories: {', '.join(missing_dirs)}")
            else:
                self.log_result("Directories List", False, f"Only {len(directories)} directories found, expected at least 5")
                
        except ImportError as e:
            self.log_result("Backlink Module Import", False, f"Cannot import backlink automation: {str(e)}")
            return
        except Exception as e:
            self.log_result("Backlink Module Import", False, f"Error testing backlink module: {str(e)}")
            return
        
        # Test 2: Playwright dependency
        try:
            import playwright
            self.log_result("Playwright Dependency", True, "Playwright is installed")
        except ImportError:
            self.log_result("Playwright Dependency", False, "Playwright is not installed - required for automation")
        
        # Test 3: Screenshot directory
        try:
            screenshot_dir = Path("/tmp/backlinks")
            screenshot_dir.mkdir(exist_ok=True)
            test_file = screenshot_dir / "test_write.txt"
            test_file.write_text("test")
            test_file.unlink()
            self.log_result("Screenshot Directory", True, f"Screenshot directory is ready and writable")
        except Exception as e:
            self.log_result("Screenshot Directory", False, f"Cannot create screenshot directory: {str(e)}")
        
        # Test 4: Business info completeness
        required_fields = ["company_name", "full_address", "phone", "email", "website", "description_short"]
        missing_fields = [field for field in required_fields if not business_info.get(field)]
        
        if not missing_fields:
            self.log_result("Business Info Completeness", True, "All required business fields are present")
        else:
            self.log_result("Business Info Completeness", False, f"Missing fields: {', '.join(missing_fields)}")
        
        # Test 5: Automation functions exist
        try:
            from backlink_automation import submit_to_hotfrog, submit_to_cylex, human_delay, human_type
            functions = ["submit_to_hotfrog", "submit_to_cylex", "human_delay", "human_type"]
            all_callable = all(callable(eval(func)) for func in functions)
            
            if all_callable:
                self.log_result("Automation Functions", True, "All automation functions are properly defined")
            else:
                self.log_result("Automation Functions", False, "Some automation functions are missing or not callable")
        except Exception as e:
            self.log_result("Automation Functions", False, f"Error checking automation functions: {str(e)}")

    def test_seo_backlink_endpoints(self):
        """Test SEO and backlink-related API endpoints"""
        print("\n🔍 TESTING SEO & BACKLINK ENDPOINTS")
        print("-" * 40)
        
        # Test backlink opportunities endpoint
        try:
            response = self.session.get(f"{BASE_URL}/seo/backlink-opportunities")
            if response.status_code == 200:
                data = response.json()
                if "directories_quebec" in data and "salon_partnerships" in data:
                    self.log_result("Backlink Opportunities API", True, f"Returns backlink strategy with {len(data)} sections")
                else:
                    self.log_result("Backlink Opportunities API", False, "Missing expected backlink data sections")
            else:
                self.log_result("Backlink Opportunities API", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_result("Backlink Opportunities API", False, f"Error: {str(e)}")
        
        # Test business info endpoint
        try:
            response = self.session.get(f"{BASE_URL}/seo/luxura-business-info")
            if response.status_code == 200:
                data = response.json()
                if "company" in data and data.get("company", {}).get("name") == "Luxura Distribution":
                    self.log_result("Business Info API", True, "Returns correct Luxura business information")
                else:
                    self.log_result("Business Info API", False, "Business info API returns incorrect data")
            else:
                self.log_result("Business Info API", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_result("Business Info API", False, f"Error: {str(e)}")
        
        # Test SEO stats endpoint
        try:
            response = self.session.get(f"{BASE_URL}/seo/stats")
            if response.status_code == 200:
                data = response.json()
                if "total_blog_posts" in data:
                    self.log_result("SEO Stats API", True, f"Returns SEO statistics with {data.get('total_blog_posts', 0)} blog posts")
                else:
                    self.log_result("SEO Stats API", False, "SEO stats missing expected data")
            else:
                self.log_result("SEO Stats API", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_result("SEO Stats API", False, f"Error: {str(e)}")

    def test_content_pipeline_endpoints(self):
        """Test Daily Content Pipeline API endpoints"""
        print("\n📰 TESTING CONTENT PIPELINE ENDPOINTS")
        print("-" * 40)
        
        # Test 1: GET /api/content/sources - Should return search queries and trusted sources
        try:
            response = self.session.get(f"{BASE_URL}/content/sources")
            if response.status_code == 200:
                data = response.json()
                required_fields = ["search_queries", "trusted_sources", "include_keywords_count"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    self.log_result("Content Sources API", True, 
                        f"Returns content sources config: {len(data.get('search_queries', []))} queries, "
                        f"{len(data.get('trusted_sources', []))} sources", data)
                else:
                    self.log_result("Content Sources API", False, f"Missing fields: {missing_fields}", data)
            else:
                self.log_result("Content Sources API", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_result("Content Sources API", False, f"Error: {str(e)}")
        
        # Test 2: GET /api/content/posts/facebook - Should list generated posts (may be empty initially)
        try:
            response = self.session.get(f"{BASE_URL}/content/posts/facebook")
            if response.status_code == 200:
                data = response.json()
                if "posts" in data and "total" in data:
                    self.log_result("Facebook Posts List API", True, 
                        f"Returns posts list: {data.get('total', 0)} posts", data)
                else:
                    self.log_result("Facebook Posts List API", False, "Missing expected fields", data)
            else:
                self.log_result("Facebook Posts List API", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_result("Facebook Posts List API", False, f"Error: {str(e)}")
        
        # Test 3: POST /api/content/jobs/daily-run - Should trigger background job
        try:
            response = self.session.post(f"{BASE_URL}/content/jobs/daily-run")
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "started":
                    self.log_result("Daily Job Trigger API", True, "Successfully triggered daily content job", data)
                else:
                    self.log_result("Daily Job Trigger API", False, f"Unexpected response: {data}")
            else:
                self.log_result("Daily Job Trigger API", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_result("Daily Job Trigger API", False, f"Error: {str(e)}")
        
        # Test 4: POST /api/content/ingest/hair-canada?max_posts=1 - Full pipeline test
        print("   🚀 Testing full content pipeline (this may take 30-60 seconds)...")
        try:
            # Use longer timeout for this endpoint as it makes real HTTP calls
            response = self.session.post(f"{BASE_URL}/content/ingest/hair-canada?max_posts=1", timeout=90)
            if response.status_code == 200:
                data = response.json()
                required_fields = ["success", "articles_found", "posts_generated", "posts"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields and data.get("success"):
                    posts = data.get("posts", [])
                    if posts:
                        # Check first post structure
                        first_post = posts[0]
                        post_fields = ["post_text", "hashtags", "confidence_score", "status"]
                        missing_post_fields = [field for field in post_fields if field not in first_post]
                        
                        if not missing_post_fields:
                            # Check for French text and hashtags
                            post_text = first_post.get("post_text", "")
                            hashtags = first_post.get("hashtags", [])
                            has_french = any(word in post_text.lower() for word in ["luxura", "extensions", "cheveux", "beauté"])
                            has_hashtags = len(hashtags) > 0
                            
                            if has_french and has_hashtags:
                                self.log_result("Content Ingest Pipeline", True, 
                                    f"Full pipeline working: {data.get('articles_found', 0)} articles found, "
                                    f"{data.get('posts_generated', 0)} posts generated with French text and hashtags", 
                                    {
                                        "articles_found": data.get("articles_found"),
                                        "posts_generated": data.get("posts_generated"),
                                        "sample_post": {
                                            "text_preview": post_text[:100] + "...",
                                            "hashtags_count": len(hashtags),
                                            "confidence_score": first_post.get("confidence_score"),
                                            "status": first_post.get("status")
                                        }
                                    })
                            else:
                                issues = []
                                if not has_french:
                                    issues.append("No French content detected")
                                if not has_hashtags:
                                    issues.append("No hashtags generated")
                                self.log_result("Content Ingest Pipeline", False, f"Content quality issues: {', '.join(issues)}", first_post)
                        else:
                            self.log_result("Content Ingest Pipeline", False, f"Generated post missing fields: {missing_post_fields}", first_post)
                    else:
                        self.log_result("Content Ingest Pipeline", False, "No posts generated despite success=true", data)
                else:
                    issues = []
                    if missing_fields:
                        issues.append(f"Missing fields: {missing_fields}")
                    if not data.get("success"):
                        issues.append("Pipeline reported failure")
                    self.log_result("Content Ingest Pipeline", False, "; ".join(issues), data)
            else:
                self.log_result("Content Ingest Pipeline", False, f"HTTP {response.status_code}: {response.text}")
        except requests.exceptions.Timeout:
            self.log_result("Content Ingest Pipeline", False, "Request timed out after 90 seconds - pipeline may be working but slow")
        except Exception as e:
            self.log_result("Content Ingest Pipeline", False, f"Error: {str(e)}")

    def test_watermark_service(self):
        """Test LUXURA watermark service and content approval endpoints"""
        print("\n🏷️ TESTING LUXURA WATERMARK SERVICE")
        print("-" * 40)
        
        # Test 1: Watermark module unit test
        print("   🧪 Testing watermark module directly...")
        try:
            # Add backend app to path
            sys.path.append('/app/backend')
            
            # Import and test the watermark function
            from app.services.watermark import process_image_with_watermark
            
            # Test with Unsplash image as specified in review request
            test_image_url = "https://images.unsplash.com/photo-1496440737103-cd596325d314?w=800"
            
            # Run the watermark function
            import asyncio
            result = asyncio.run(process_image_with_watermark(test_image_url))
            
            if result and isinstance(result, bytes):
                result_size = len(result)
                if result_size > 100000:  # > 100KB as specified
                    self.log_result("Watermark Module Unit Test", True, 
                        f"Watermark function working: generated {result_size} bytes (>{result_size//1024}KB)", 
                        {"image_size_bytes": result_size, "image_size_kb": result_size//1024})
                else:
                    self.log_result("Watermark Module Unit Test", False, 
                        f"Image too small: {result_size} bytes (<100KB)", 
                        {"image_size_bytes": result_size})
            else:
                self.log_result("Watermark Module Unit Test", False, 
                    f"Watermark function returned invalid result: {type(result)}")
                    
        except ImportError as e:
            self.log_result("Watermark Module Unit Test", False, f"Cannot import watermark module: {str(e)}")
        except Exception as e:
            self.log_result("Watermark Module Unit Test", False, f"Watermark test failed: {str(e)}")
        
        # Test 2: GET /api/content/pending - Should return pending posts list
        try:
            response = self.session.get(f"{BASE_URL}/content/pending")
            if response.status_code == 200:
                data = response.json()
                if "pending_count" in data and "posts" in data:
                    self.log_result("Content Pending API", True, 
                        f"Returns pending posts: {data.get('pending_count', 0)} posts", data)
                else:
                    self.log_result("Content Pending API", False, "Missing expected fields", data)
            else:
                self.log_result("Content Pending API", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_result("Content Pending API", False, f"Error: {str(e)}")
        
        # Test 3: POST /api/content/test-approval-flow - Should create test post and return URLs
        try:
            response = self.session.post(f"{BASE_URL}/content/test-approval-flow")
            if response.status_code == 200:
                data = response.json()
                required_fields = ["success", "post_id", "approve_url", "reject_url"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields and data.get("success"):
                    post_id = data.get("post_id")
                    approve_url = data.get("approve_url")
                    reject_url = data.get("reject_url")
                    
                    # Validate URLs contain the post_id
                    if post_id in approve_url and post_id in reject_url:
                        self.log_result("Content Test Approval Flow", True, 
                            f"Test approval flow created successfully: post_id={post_id}", 
                            {
                                "post_id": post_id,
                                "approve_url": approve_url,
                                "reject_url": reject_url
                            })
                    else:
                        self.log_result("Content Test Approval Flow", False, 
                            "URLs don't contain post_id", data)
                else:
                    issues = []
                    if missing_fields:
                        issues.append(f"Missing fields: {missing_fields}")
                    if not data.get("success"):
                        issues.append("Flow reported failure")
                    self.log_result("Content Test Approval Flow", False, "; ".join(issues), data)
            else:
                self.log_result("Content Test Approval Flow", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_result("Content Test Approval Flow", False, f"Error: {str(e)}")
        
        # Test 4: Verify watermark integration in approval endpoint (without actually approving)
        print("   🔍 Testing watermark integration readiness...")
        try:
            # Check if the approval endpoint exists by testing with a fake post_id
            # This should return 404 but confirm the endpoint exists
            fake_post_id = "test-watermark-integration-check"
            response = self.session.get(f"{BASE_URL}/content/approve/{fake_post_id}")
            
            # We expect 404 for non-existent post, but endpoint should exist
            if response.status_code == 404:
                # Check if the response is HTML (indicating the endpoint exists)
                if "text/html" in response.headers.get("content-type", ""):
                    self.log_result("Watermark Integration Readiness", True, 
                        "Approval endpoint exists and ready for watermark integration")
                else:
                    self.log_result("Watermark Integration Readiness", False, 
                        "Approval endpoint exists but not returning HTML response")
            elif response.status_code == 500:
                # Server error might indicate watermark integration issues
                self.log_result("Watermark Integration Readiness", False, 
                    f"Approval endpoint has server error: {response.text}")
            else:
                self.log_result("Watermark Integration Readiness", False, 
                    f"Unexpected response from approval endpoint: {response.status_code}")
                    
        except Exception as e:
            self.log_result("Watermark Integration Readiness", False, f"Error testing approval endpoint: {str(e)}")
        
        # Test 5: Check watermark dependencies
        try:
            from PIL import Image, ImageDraw, ImageFont
            import httpx
            self.log_result("Watermark Dependencies", True, "All watermark dependencies available (PIL, httpx)")
        except ImportError as e:
            self.log_result("Watermark Dependencies", False, f"Missing watermark dependencies: {str(e)}")
        
        # Test 6: Test image format validation
        try:
            # Test that watermark can handle JPEG format
            from app.services.watermark import create_gold_text_watermark
            from PIL import Image
            import io
            
            # Create a test image
            test_img = Image.new('RGB', (800, 600), color='white')
            watermarked = create_gold_text_watermark(test_img, "LUXURA", "bottom-right", 0.35)
            
            # Convert to JPEG bytes
            output = io.BytesIO()
            if watermarked.mode == 'RGBA':
                background = Image.new('RGB', watermarked.size, (255, 255, 255))
                background.paste(watermarked, mask=watermarked.split()[3])
                watermarked = background
            
            watermarked.save(output, format='JPEG', quality=95)
            jpeg_bytes = output.getvalue()
            
            if len(jpeg_bytes) > 10000:  # Should be reasonable size
                self.log_result("Watermark JPEG Format", True, 
                    f"JPEG watermark generation working: {len(jpeg_bytes)} bytes")
            else:
                self.log_result("Watermark JPEG Format", False, 
                    f"JPEG output too small: {len(jpeg_bytes)} bytes")
                    
        except Exception as e:
            self.log_result("Watermark JPEG Format", False, f"JPEG format test failed: {str(e)}")

    def run_all_tests(self):
        """Run all tests including backlink automation"""
        print("🚀 Starting Luxura Distribution Complete Testing Suite")
        print("=" * 60)
        
        # Core API Tests
        print("\n📡 TESTING CORE APIs")
        print("-" * 30)
        self.test_health_check()
        self.test_products_list()
        self.test_single_product()
        self.test_products_filter()
        self.test_categories()
        self.test_blog_list()
        self.test_single_blog_post()
        self.test_salons()
        
        # Auth Tests (expect 401 for protected endpoints)
        print("\n🔐 TESTING AUTH PROTECTION")
        print("-" * 30)
        self.test_auth_endpoints()
        self.test_cart_unauthorized()
        
        # SEO & Backlink Tests
        self.test_seo_backlink_endpoints()
        
        # Content Pipeline Tests
        self.test_content_pipeline_endpoints()
        
        # Watermark Service Tests
        self.test_watermark_service()
        
        # Backlink Automation Tests
        self.test_backlink_automation_system()
        
        # Print Enhanced Summary
        print("\n" + "=" * 60)
        print("📊 COMPLETE TEST SUMMARY")
        print("=" * 60)
        print(f"✅ PASSED: {self.passed_tests}")
        print(f"❌ FAILED: {self.total_tests - self.passed_tests}")
        print(f"📈 TOTAL: {self.total_tests}")
        
        # Categorize results
        api_tests = [r for r in self.results if "API" in r["test"] or "Health" in r["test"]]
        backlink_tests = [r for r in self.results if "Backlink" in r["test"] or "Playwright" in r["test"] or "Screenshot" in r["test"]]
        seo_tests = [r for r in self.results if "SEO" in r["test"] or "Business Info" in r["test"]]
        
        api_passed = len([r for r in api_tests if r["success"]])
        backlink_passed = len([r for r in backlink_tests if r["success"]])
        seo_passed = len([r for r in seo_tests if r["success"]])
        
        print(f"\n📊 BREAKDOWN:")
        print(f"   🔌 Core APIs: {api_passed}/{len(api_tests)} passed")
        print(f"   🔗 Backlink System: {backlink_passed}/{len(backlink_tests)} passed")
        print(f"   🔍 SEO Features: {seo_passed}/{len(seo_tests)} passed")
        
        # Critical Issues
        critical_failures = [r for r in self.results if not r["success"] and any(keyword in r["test"] for keyword in ["Health", "Import", "Playwright"])]
        
        if critical_failures:
            print(f"\n🚨 CRITICAL ISSUES ({len(critical_failures)}):")
            for failure in critical_failures:
                print(f"   • {failure['test']}: {failure['message']}")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        
        playwright_failed = any("Playwright" in r["test"] and not r["success"] for r in self.results)
        if playwright_failed:
            print("   • Install Playwright: pip install playwright && playwright install")
        
        if self.passed_tests == self.total_tests:
            print("   • 🎉 ALL SYSTEMS OPERATIONAL! Ready for directory submissions.")
            print("   • Consider adding API endpoints for backlink automation")
        elif self.passed_tests >= self.total_tests * 0.8:
            print("   • ✅ Most systems working. Fix critical issues before production.")
        else:
            print("   • ⚠️ Multiple issues detected. Review and fix before proceeding.")
        
        return self.results

if __name__ == "__main__":
    print(f"Testing backend API at: {BASE_URL}")
    tester = LuxuraAPITester()
    results = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if tester.passed_tests == tester.total_tests else 1)