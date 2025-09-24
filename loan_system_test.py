import requests
import sys
import json
from datetime import datetime, timedelta

class LoanSystemTester:
    def __init__(self, base_url="https://scholibooks.preview.emergentagent.com"):
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

    def create_and_login_user(self):
        """Create and login a test user"""
        timestamp = datetime.now().strftime('%H%M%S')
        user_data = {
            "email": f"loanuser_{timestamp}@test.com",
            "password": "loanpass123",
            "full_name": f"Loan Test User {timestamp}",
            "role": "user"
        }
        
        success, response = self.run_test(
            "Create Loan Test User",
            "POST",
            "auth/register",
            200,
            data=user_data
        )
        
        if success:
            # Login
            success, response = self.run_test(
                "Login Loan Test User",
                "POST",
                "auth/login",
                200,
                data={"email": user_data["email"], "password": user_data["password"]}
            )
            
            if success and 'access_token' in response:
                self.token = response['access_token']
                return True, response['user']
        
        return False, None

    def create_school_admin_and_login(self):
        """Create school admin for book creation"""
        timestamp = datetime.now().strftime('%H%M%S')
        school_data = {
            "name": f"École Loan Test {timestamp}",
            "address": "789 Rue des Emprunts, 75003 Paris",
            "country": "France",
            "description": "École pour tester le système d'emprunts",
            "admin_email": f"admin.loan.{timestamp}@ecole-test.fr",
            "admin_name": f"Admin Loan {timestamp}",
            "admin_password": "loanadmin123"
        }
        
        # Clear token for school registration
        saved_token = self.token
        self.token = None
        
        success, response = self.run_test(
            "Create School for Loan Testing",
            "POST",
            "schools",
            200,
            data=school_data
        )
        
        if success:
            # Login as school admin
            success, response = self.run_test(
                "Login School Admin for Loan Testing",
                "POST",
                "auth/login",
                200,
                data={"email": school_data["admin_email"], "password": school_data["admin_password"]}
            )
            
            if success and 'access_token' in response:
                self.token = response['access_token']
                return True, (response['user'], school_data)
        
        # Restore token if failed
        self.token = saved_token
        return False, None

    def create_test_books(self, school_id):
        """Create test books for loan testing"""
        books_created = []
        
        # Create physical book with multiple copies
        physical_book_data = {
            "title": "Guide des Emprunts Physiques",
            "authors": ["Expert Bibliothèque"],
            "isbn": "978-2-444444-44-4",
            "description": "Un guide complet pour comprendre les emprunts physiques",
            "categories": ["Guide", "Éducation"],
            "language": "fr",
            "format": "physical",
            "price": 18.50,
            "school_id": school_id,
            "physical_copies": 3
        }
        
        success, response = self.run_test(
            "Create Physical Book for Loan Testing",
            "POST",
            "books",
            200,
            data=physical_book_data
        )
        
        if success and response:
            books_created.append({"type": "physical", "data": response})
        
        # Create digital book
        digital_book_data = {
            "title": "Manuel Numérique des Téléchargements",
            "authors": ["Expert Digital"],
            "isbn": "978-2-555555-55-5",
            "description": "Un manuel numérique pour les téléchargements gratuits",
            "categories": ["Manuel", "Numérique"],
            "language": "fr",
            "format": "digital",
            "price": 0.0,
            "school_id": school_id,
            "physical_copies": 0
        }
        
        success, response = self.run_test(
            "Create Digital Book for Loan Testing",
            "POST",
            "books",
            200,
            data=digital_book_data
        )
        
        if success and response:
            books_created.append({"type": "digital", "data": response})
        
        return books_created

    def test_get_my_loans(self):
        """Test getting user's loans"""
        success, response = self.run_test(
            "Get My Loans",
            "GET",
            "loans/my",
            200
        )
        return success, response if success else None

    def test_reserve_physical_book(self, book_id):
        """Test reserving a physical book"""
        success, response = self.run_test(
            f"Reserve Physical Book ({book_id})",
            "POST",
            "loans/reserve",
            200,
            data={"book_id": book_id}
        )
        return success, response if success else None

    def test_update_loan_status(self, loan_id, status):
        """Test updating loan status"""
        success, response = self.run_test(
            f"Update Loan Status to {status}",
            "PUT",
            f"loans/{loan_id}/status?status={status}",
            200
        )
        return success, response if success else None

    def test_digital_book_download(self, book_id):
        """Test downloading digital book"""
        success, response = self.run_test(
            f"Download Digital Book ({book_id})",
            "POST",
            f"books/{book_id}/download",
            200
        )
        return success, response if success else None

    def test_multiple_reservations_same_book(self, book_id):
        """Test that user cannot reserve same book twice"""
        success, response = self.run_test(
            f"Try Double Reservation (Should Fail)",
            "POST",
            "loans/reserve",
            400,
            data={"book_id": book_id}
        )
        return success, response if success else None

    def run_loan_system_tests(self):
        """Run all loan system tests"""
        print("🚀 Starting Loan System API Tests")
        print("=" * 50)

        # Test 1: Create school admin and books
        print("\n🎓 Setting up School Admin and Books...")
        admin_success, admin_data = self.create_school_admin_and_login()
        
        if not admin_success:
            print("❌ Cannot proceed without school admin")
            return False

        admin_user, school_data = admin_data
        school_id = admin_user.get('school_id')
        
        if not school_id:
            print("❌ School admin has no school_id")
            return False

        # Create test books
        print("\n📚 Creating Test Books...")
        test_books = self.create_test_books(school_id)
        
        if not test_books:
            print("❌ No test books created")
            return False

        # Test 2: Create regular user for loan testing
        print("\n👤 Creating Regular User for Loan Testing...")
        user_success, user_info = self.create_and_login_user()
        
        if not user_success:
            print("❌ Cannot proceed without regular user")
            return False

        # Test 3: Test empty loans list
        print("\n📋 Testing Empty Loans List...")
        self.test_get_my_loans()

        # Test 4: Reserve physical books
        physical_books = [book for book in test_books if book['type'] == 'physical']
        loan_ids = []
        
        if physical_books:
            print("\n📋 Testing Physical Book Reservations...")
            for book in physical_books:
                success, response = self.test_reserve_physical_book(book['data']['id'])
                if success and response and 'loan_id' in response:
                    loan_ids.append(response['loan_id'])

        # Test 5: Test loans list after reservations
        print("\n📋 Testing Loans List After Reservations...")
        self.test_get_my_loans()

        # Test 6: Test double reservation (should fail)
        if physical_books:
            print("\n🚫 Testing Double Reservation Prevention...")
            self.test_multiple_reservations_same_book(physical_books[0]['data']['id'])

        # Test 7: Test digital book downloads
        digital_books = [book for book in test_books if book['type'] == 'digital']
        if digital_books:
            print("\n💾 Testing Digital Book Downloads...")
            for book in digital_books:
                self.test_digital_book_download(book['data']['id'])

        # Test 8: Test loan status updates (as school admin)
        if loan_ids:
            print("\n🔄 Testing Loan Status Updates (as School Admin)...")
            # Switch back to school admin token
            admin_success, admin_info = self.run_test(
                "Re-login School Admin for Status Updates",
                "POST",
                "auth/login",
                200,
                data={"email": school_data["admin_email"], "password": school_data["admin_password"]}
            )
            
            if admin_success and 'access_token' in admin_info:
                self.token = admin_info['access_token']
                
                # Update first loan to borrowed
                if loan_ids:
                    self.test_update_loan_status(loan_ids[0], "borrowed")
                    
                    # Update to returned
                    self.test_update_loan_status(loan_ids[0], "returned")

        # Print final results
        print("\n" + "=" * 50)
        print("📊 LOAN SYSTEM TEST RESULTS")
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
    tester = LoanSystemTester()
    success = tester.run_loan_system_tests()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())