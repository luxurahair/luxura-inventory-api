#!/usr/bin/env python3
"""
Backend API Testing for Luxura Distribution
Tests all backend endpoints to verify functionality
"""

import requests
import json
import sys
from datetime import datetime

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
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.total_tests - self.passed_tests}")
        print(f"Success Rate: {(self.passed_tests / self.total_tests * 100):.1f}%")
        
        # Failed tests details
        failed_tests = [r for r in self.results if not r["success"]]
        if failed_tests:
            print(f"\n❌ FAILED TESTS ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"  - {test['test']}: {test['message']}")
        
        return self.results

if __name__ == "__main__":
    print(f"Testing backend API at: {BASE_URL}")
    tester = LuxuraAPITester()
    results = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if tester.passed_tests == tester.total_tests else 1)