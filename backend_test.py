import requests
import sys
import json
from datetime import datetime, timedelta

class SchoolLibraryAPITester:
    def __init__(self, base_url="https://edubliotheque.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
        
        self.test_results.append({
            "name": name,
            "success": success,
            "details": details
        })

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        
        if headers:
            test_headers.update(headers)

        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=10)

            success = response.status_code == expected_status
            
            if success:
                self.log_test(name, True)
                try:
                    return True, response.json()
                except:
                    return True, response.text
            else:
                error_msg = f"Expected {expected_status}, got {response.status_code}"
                try:
                    error_detail = response.json()
                    error_msg += f" - {error_detail}"
                except:
                    error_msg += f" - {response.text[:200]}"
                
                self.log_test(name, False, error_msg)
                return False, {}

        except Exception as e:
            self.log_test(name, False, f"Request failed: {str(e)}")
            return False, {}

    def test_user_registration(self):
        """Test user registration"""
        test_user_data = {
            "email": f"testuser_{datetime.now().strftime('%H%M%S')}@test.com",
            "password": "testpass123",
            "full_name": "Test User",
            "phone": "0123456789",
            "role": "user"
        }
        
        success, response = self.run_test(
            "User Registration",
            "POST",
            "auth/register",
            200,
            data=test_user_data
        )
        
        return success, test_user_data if success else None

    def test_user_login(self, email, password):
        """Test user login and get token"""
        success, response = self.run_test(
            "User Login",
            "POST",
            "auth/login",
            200,
            data={"email": email, "password": password}
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            return True, response['user']
        return False, None

    def test_get_current_user(self):
        """Test getting current user info"""
        success, response = self.run_test(
            "Get Current User",
            "GET",
            "auth/me",
            200
        )
        return success, response if success else None

    def test_school_registration(self):
        """Test school registration"""
        timestamp = datetime.now().strftime('%H%M%S')
        school_data = {
            "name": f"École Test {timestamp}",
            "address": "123 Rue de Test, 75001 Paris",
            "country": "France",
            "description": "École de test pour les API",
            "admin_email": f"admin.test.{timestamp}@ecole-test.fr",
            "admin_name": f"Admin Test {timestamp}",
            "admin_password": "adminpass123"
        }
        
        success, response = self.run_test(
            "School Registration",
            "POST",
            "schools",
            200,
            data=school_data
        )
        
        return success, (response, school_data) if success else None

    def test_get_schools(self):
        """Test getting schools list"""
        success, response = self.run_test(
            "Get Schools List",
            "GET",
            "schools",
            200
        )
        return success, response if success else None

    def test_dashboard_stats(self):
        """Test dashboard statistics"""
        success, response = self.run_test(
            "Dashboard Statistics",
            "GET",
            "dashboard/stats",
            200
        )
        return success, response if success else None

    def test_super_admin_login(self):
        """Test super admin login"""
        return self.test_user_login("superadmin@schoollibrary.com", "admin123")

    def test_school_admin_login(self):
        """Test school admin login"""
        return self.test_user_login("marie.dupont@ecole-arts.fr", "marie123")

    def test_book_creation(self):
        """Test book creation (requires school admin or librarian)"""
        book_data = {
            "title": "Livre de Test",
            "authors": ["Auteur Test"],
            "isbn": "978-2-123456-78-9",
            "description": "Un livre de test pour l'API",
            "categories": ["Fiction", "Test"],
            "language": "fr",
            "format": "physical",
            "price": 15.99,
            "school_id": "test-school-id",
            "physical_copies": 3
        }
        
        success, response = self.run_test(
            "Book Creation",
            "POST",
            "books",
            200,
            data=book_data
        )
        return success, response if success else None

    def test_get_books(self):
        """Test getting books list"""
        success, response = self.run_test(
            "Get Books List",
            "GET",
            "books",
            200
        )
        return success, response if success else None

    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting School Library API Tests")
        print("=" * 50)

        # Test 1: User Registration
        print("\n📝 Testing User Registration...")
        user_success, test_user = self.test_user_registration()

        # Test 2: User Login with test user
        if user_success and test_user:
            print("\n🔐 Testing User Login with test user...")
            login_success, user_info = self.test_user_login(test_user['email'], test_user['password'])
            
            if login_success:
                # Test 3: Get current user
                print("\n👤 Testing Get Current User...")
                self.test_get_current_user()

        # Test 4: Super Admin Login
        print("\n👑 Testing Super Admin Login...")
        super_admin_success, super_admin_info = self.test_super_admin_login()
        
        if super_admin_success:
            # Test 5: Dashboard stats as super admin
            print("\n📊 Testing Dashboard Stats (Super Admin)...")
            self.test_dashboard_stats()
            
            # Test 6: Get schools as super admin
            print("\n🏫 Testing Get Schools (Super Admin)...")
            self.test_get_schools()

        # Test 7: School Registration (no auth required)
        print("\n🏫 Testing School Registration...")
        self.token = None  # Clear token for school registration
        school_success, school_data = self.test_school_registration()

        # Test 8: School Admin Login
        print("\n🎓 Testing School Admin Login...")
        school_admin_success, school_admin_info = self.test_school_admin_login()
        
        if school_admin_success:
            # Test 9: Dashboard stats as school admin
            print("\n📊 Testing Dashboard Stats (School Admin)...")
            self.test_dashboard_stats()
            
            # Test 10: Book creation as school admin
            print("\n📚 Testing Book Creation (School Admin)...")
            self.test_book_creation()

        # Test 11: Get books (public endpoint)
        print("\n📖 Testing Get Books List...")
        self.test_get_books()

        # Print final results
        print("\n" + "=" * 50)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 50)
        print(f"Total tests run: {self.tests_run}")
        print(f"Tests passed: {self.tests_passed}")
        print(f"Tests failed: {self.tests_run - self.tests_passed}")
        print(f"Success rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        # Print failed tests
        failed_tests = [test for test in self.test_results if not test['success']]
        if failed_tests:
            print("\n❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"   - {test['name']}: {test['details']}")
        
        return self.tests_passed == self.tests_run

def main():
    """Main test function"""
    tester = SchoolLibraryAPITester()
    success = tester.run_all_tests()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())