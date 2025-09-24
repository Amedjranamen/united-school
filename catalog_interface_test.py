#!/usr/bin/env python3
"""
Test spécifique pour l'interface catalogue avec les nouveaux endpoints
Conformément à la demande de test dans le review_request
"""

import requests
import sys
import json
from datetime import datetime

class CatalogInterfaceTest:
    def __init__(self, base_url="https://scholivre.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.test_results = []

    def log_result(self, test_name, success, details=""):
        """Log test result"""
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status} - {test_name}")
        if not success:
            print(f"   Details: {details}")
        
        self.test_results.append({
            "name": test_name,
            "success": success,
            "details": details
        })

    def make_request(self, method, endpoint, data=None, expected_status=200):
        """Make API request"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            
            success = response.status_code == expected_status
            
            if success:
                try:
                    return True, response.json()
                except:
                    return True, response.text
            else:
                try:
                    error_detail = response.json()
                except:
                    error_detail = response.text[:200]
                
                return False, f"Expected {expected_status}, got {response.status_code} - {error_detail}"

        except Exception as e:
            return False, f"Request failed: {str(e)}"

    def test_authentication_flow(self):
        """Test 1: Authentification fonctionnelle"""
        print("\n🔐 Test 1: Authentification fonctionnelle")
        
        # Create test user
        timestamp = datetime.now().strftime('%H%M%S')
        user_data = {
            "email": f"testuser_{timestamp}@test.com",
            "password": "testpass123",
            "full_name": "Test User Catalogue",
            "role": "user"
        }
        
        success, response = self.make_request("POST", "auth/register", user_data)
        self.log_result("POST /api/auth/register", success, response if not success else "")
        
        if not success:
            return False
        
        # Test login
        login_data = {"email": user_data["email"], "password": user_data["password"]}
        success, response = self.make_request("POST", "auth/login", login_data)
        self.log_result("POST /api/auth/login", success, response if not success else "")
        
        if success and isinstance(response, dict) and 'access_token' in response:
            self.token = response['access_token']
            
            # Test /auth/me
            success, response = self.make_request("GET", "auth/me")
            self.log_result("GET /api/auth/me", success, response if not success else "")
            return success
        
        return False

    def test_catalog_api(self):
        """Test 2: API catalogue fonctionnelle"""
        print("\n📚 Test 2: API catalogue fonctionnelle")
        
        # Test GET /api/books
        success, response = self.make_request("GET", "books")
        self.log_result("GET /api/books", success, response if not success else "")
        
        books = []
        if success and isinstance(response, list):
            books = response
            print(f"   Found {len(books)} books in catalog")
        
        # Test GET /api/books/{id} with existing book
        if books:
            book_id = books[0]['id']
            success, response = self.make_request("GET", f"books/{book_id}")
            self.log_result(f"GET /api/books/{book_id}", success, response if not success else "")
        else:
            print("   ⚠️ No books found to test individual book retrieval")
        
        return len(books) > 0

    def test_new_catalog_endpoints(self, books):
        """Test 3: Nouveaux endpoints pour le catalogue"""
        print("\n🆕 Test 3: Nouveaux endpoints pour le catalogue")
        
        physical_books = [book for book in books if book.get('format') in ['physical', 'both']]
        digital_books = [book for book in books if book.get('format') in ['digital', 'both']]
        
        # Test POST /api/loans/reserve
        if physical_books:
            book_id = physical_books[0]['id']
            reserve_data = {"book_id": book_id}
            success, response = self.make_request("POST", "loans/reserve", reserve_data)
            self.log_result(f"POST /api/loans/reserve (book: {book_id})", success, response if not success else "")
        else:
            print("   ⚠️ No physical books found to test reservation")
        
        # Test POST /api/books/{id}/download
        if digital_books:
            book_id = digital_books[0]['id']
            success, response = self.make_request("POST", f"books/{book_id}/download")
            # Note: This might fail if no file is uploaded, which is expected
            expected_status = 200 if 'file_path' in digital_books[0] else 404
            success, response = self.make_request("POST", f"books/{book_id}/download", expected_status=expected_status)
            self.log_result(f"POST /api/books/{book_id}/download", success, response if not success else "")
            
            # Test GET /api/books/{id}/file
            success, response = self.make_request("GET", f"books/{book_id}/file", expected_status=expected_status)
            self.log_result(f"GET /api/books/{book_id}/file", success, response if not success else "")
        else:
            print("   ⚠️ No digital books found to test download")

    def test_error_handling(self):
        """Test 4: Gestion erreurs"""
        print("\n❌ Test 4: Gestion erreurs")
        
        # Test 404 errors
        success, response = self.make_request("GET", "books/nonexistent-id", expected_status=404)
        self.log_result("GET /api/books/nonexistent-id (404)", success, response if not success else "")
        
        success, response = self.make_request("POST", "loans/reserve", {"book_id": "nonexistent-id"}, expected_status=404)
        self.log_result("POST /api/loans/reserve nonexistent book (404)", success, response if not success else "")
        
        # Test 400 errors
        success, response = self.make_request("POST", "loans/reserve", {}, expected_status=400)
        self.log_result("POST /api/loans/reserve without book_id (400)", success, response if not success else "")
        
        # Test 403 errors (unauthorized)
        saved_token = self.token
        self.token = None
        
        success, response = self.make_request("GET", "auth/me", expected_status=403)
        self.log_result("GET /api/auth/me without token (403)", success, response if not success else "")
        
        success, response = self.make_request("POST", "loans/reserve", {"book_id": "test"}, expected_status=403)
        self.log_result("POST /api/loans/reserve without token (403)", success, response if not success else "")
        
        self.token = saved_token

    def run_all_tests(self):
        """Run all catalog interface tests"""
        print("🚀 Test Interface Catalogue Complet")
        print("=" * 60)
        print("Backend FastAPI + MongoDB avec nouveaux endpoints")
        print("Configuration: Backend sur port 8001 avec préfixe /api")
        print("=" * 60)

        # Test 1: Authentication
        auth_success = self.test_authentication_flow()
        
        if not auth_success:
            print("\n❌ Authentication failed - cannot continue with other tests")
            return False

        # Test 2: Catalog API
        success, books_response = self.make_request("GET", "books")
        books = books_response if success and isinstance(books_response, list) else []
        
        self.test_catalog_api()
        
        # Test 3: New endpoints
        if books:
            self.test_new_catalog_endpoints(books)
        else:
            print("\n⚠️ No books found - skipping new endpoint tests")
        
        # Test 4: Error handling
        self.test_error_handling()

        # Summary
        print("\n" + "=" * 60)
        print("📊 RÉSUMÉ DES TESTS")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for test in self.test_results if test['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total des tests: {total_tests}")
        print(f"Tests réussis: {passed_tests}")
        print(f"Tests échoués: {failed_tests}")
        print(f"Taux de réussite: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ TESTS ÉCHOUÉS:")
            for test in self.test_results:
                if not test['success']:
                    print(f"   - {test['name']}: {test['details']}")
        
        print(f"\n✅ CONCLUSION:")
        if passed_tests == total_tests:
            print("   Tous les tests sont passés - Interface catalogue prête!")
        elif passed_tests >= total_tests * 0.8:
            print("   La plupart des tests sont passés - Interface catalogue fonctionnelle avec quelques limitations")
        else:
            print("   Plusieurs tests ont échoué - Interface catalogue nécessite des corrections")
        
        return passed_tests >= total_tests * 0.8

def main():
    """Main test function"""
    tester = CatalogInterfaceTest()
    success = tester.run_all_tests()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())