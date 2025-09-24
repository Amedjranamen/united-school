import requests
import sys
import json
from datetime import datetime, timedelta

class SchoolLibraryAPITester:
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

    def test_get_book_by_id(self, book_id):
        """Test getting a specific book by ID"""
        success, response = self.run_test(
            f"Get Book by ID ({book_id})",
            "GET",
            f"books/{book_id}",
            200
        )
        return success, response if success else None

    def test_get_book_by_invalid_id(self):
        """Test getting a book with invalid ID (should return 404)"""
        success, response = self.run_test(
            "Get Book by Invalid ID",
            "GET",
            "books/invalid-book-id-123",
            404
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

    def test_reserve_nonexistent_book(self):
        """Test reserving a non-existent book (should return 404)"""
        success, response = self.run_test(
            "Reserve Non-existent Book",
            "POST",
            "loans/reserve",
            404,
            data={"book_id": "nonexistent-book-id"}
        )
        return success, response if success else None

    def test_reserve_without_book_id(self):
        """Test reservation without book_id (should return 400)"""
        success, response = self.run_test(
            "Reserve Without Book ID",
            "POST",
            "loans/reserve",
            400,
            data={}
        )
        return success, response if success else None

    def test_download_digital_book(self, book_id):
        """Test downloading a digital book"""
        success, response = self.run_test(
            f"Download Digital Book ({book_id})",
            "POST",
            f"books/{book_id}/download",
            200
        )
        return success, response if success else None

    def test_download_nonexistent_book(self):
        """Test downloading a non-existent book (should return 404)"""
        success, response = self.run_test(
            "Download Non-existent Book",
            "POST",
            "books/nonexistent-book-id/download",
            404
        )
        return success, response if success else None

    def test_serve_book_file(self, book_id):
        """Test serving book file"""
        success, response = self.run_test(
            f"Serve Book File ({book_id})",
            "GET",
            f"books/{book_id}/file",
            200
        )
        return success, response if success else None

    def test_serve_nonexistent_book_file(self):
        """Test serving file for non-existent book (should return 404)"""
        success, response = self.run_test(
            "Serve Non-existent Book File",
            "GET",
            "books/nonexistent-book-id/file",
            404
        )
        return success, response if success else None

    def test_upload_book_file(self, book_id, file_content=b"Test PDF content", filename="test.pdf"):
        """Test uploading a file to a book"""
        url = f"{self.api_url}/books/{book_id}/upload-file"
        headers = {}
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        print(f"\n🔍 Testing Upload Book File ({book_id})...")
        print(f"   URL: {url}")
        
        try:
            files = {'file': (filename, file_content, 'application/pdf')}
            response = requests.post(url, files=files, headers=headers, timeout=10)
            
            success = response.status_code == 200
            
            if success:
                self.log_test(f"Upload Book File ({book_id})", True)
                try:
                    return True, response.json()
                except:
                    return True, response.text
            else:
                error_msg = f"Expected 200, got {response.status_code}"
                try:
                    error_detail = response.json()
                    error_msg += f" - {error_detail}"
                except:
                    error_msg += f" - {response.text[:200]}"
                
                self.log_test(f"Upload Book File ({book_id})", False, error_msg)
                return False, {}

        except Exception as e:
            self.log_test(f"Upload Book File ({book_id})", False, f"Request failed: {str(e)}")
            return False, {}

    def test_upload_invalid_file_format(self, book_id):
        """Test uploading invalid file format (should return 400)"""
        url = f"{self.api_url}/books/{book_id}/upload-file"
        headers = {}
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        print(f"\n🔍 Testing Upload Invalid File Format ({book_id})...")
        print(f"   URL: {url}")
        
        try:
            files = {'file': ('test.txt', b"Invalid text content", 'text/plain')}
            response = requests.post(url, files=files, headers=headers, timeout=10)
            
            success = response.status_code == 400
            
            if success:
                self.log_test(f"Upload Invalid File Format ({book_id})", True)
                try:
                    return True, response.json()
                except:
                    return True, response.text
            else:
                error_msg = f"Expected 400, got {response.status_code}"
                try:
                    error_detail = response.json()
                    error_msg += f" - {error_detail}"
                except:
                    error_msg += f" - {response.text[:200]}"
                
                self.log_test(f"Upload Invalid File Format ({book_id})", False, error_msg)
                return False, {}

        except Exception as e:
            self.log_test(f"Upload Invalid File Format ({book_id})", False, f"Request failed: {str(e)}")
            return False, {}

    def test_complete_digital_book_flow(self, school_id=None):
        """Test complete digital book flow: create → upload → verify file_path → download"""
        print("\n🎯 TESTING COMPLETE DIGITAL BOOK FLOW")
        print("=" * 50)
        
        # If no school_id provided, try to get it from current user
        if not school_id:
            success, user_info = self.test_get_current_user()
            if success and user_info and user_info.get('school_id'):
                school_id = user_info['school_id']
            else:
                print("⚠️ Warning: No school_id available for digital book flow test")
                return False
        
        # Step 1: Create a digital book
        digital_book_data = {
            "title": "Livre Numérique Upload Test",
            "authors": ["Auteur Upload Test"],
            "isbn": "978-2-444444-44-4",
            "description": "Un livre numérique pour tester l'upload complet",
            "categories": ["Test", "Upload"],
            "language": "fr",
            "format": "digital",
            "price": 0.0,
            "school_id": school_id,
            "physical_copies": 0
        }
        
        print("\n📚 Step 1: Creating digital book...")
        success, book_response = self.run_test(
            "Create Digital Book for Upload Test",
            "POST",
            "books",
            200,
            data=digital_book_data
        )
        
        if not success or not book_response:
            print("❌ Failed to create digital book - aborting flow test")
            return False
        
        book_id = book_response['id']
        print(f"✅ Digital book created with ID: {book_id}")
        
        # Step 2: Verify book has no file_path initially
        print("\n🔍 Step 2: Verifying book has no file_path initially...")
        success, book_details = self.test_get_book_by_id(book_id)
        
        if success and book_details:
            has_file_path = 'file_path' in book_details and book_details['file_path']
            if has_file_path:
                print(f"⚠️ Warning: Book already has file_path: {book_details['file_path']}")
            else:
                print("✅ Confirmed: Book has no file_path initially")
        
        # Step 3: Upload a file
        print("\n📤 Step 3: Uploading PDF file...")
        test_pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000074 00000 n \n0000000120 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n179\n%%EOF"
        
        upload_success, upload_response = self.test_upload_book_file(book_id, test_pdf_content, "test_book.pdf")
        
        if not upload_success:
            print("❌ Failed to upload file - aborting flow test")
            return False
        
        print("✅ File uploaded successfully")
        
        # Step 4: Verify book now has file_path
        print("\n🔍 Step 4: Verifying book now has file_path...")
        success, updated_book_details = self.test_get_book_by_id(book_id)
        
        if success and updated_book_details:
            has_file_path = 'file_path' in updated_book_details and updated_book_details['file_path']
            if has_file_path:
                print(f"✅ SUCCESS: Book now has file_path: {updated_book_details['file_path']}")
                file_path = updated_book_details['file_path']
            else:
                print("❌ CRITICAL ISSUE: Book still has no file_path after upload!")
                self.log_test("Digital Book Flow - File Path Update", False, "Book has no file_path after successful upload")
                return False
        else:
            print("❌ Failed to retrieve updated book details")
            return False
        
        # Step 5: Test download endpoint
        print("\n💾 Step 5: Testing download endpoint...")
        download_success, download_response = self.test_download_digital_book(book_id)
        
        if not download_success:
            print("❌ Download endpoint failed")
            return False
        
        print("✅ Download endpoint working")
        
        # Step 6: Test file serving endpoint
        print("\n📁 Step 6: Testing file serving endpoint...")
        serve_success, serve_response = self.test_serve_book_file(book_id)
        
        if not serve_success:
            print("❌ File serving endpoint failed")
            return False
        
        print("✅ File serving endpoint working")
        
        # Step 7: Test with EPUB file
        print("\n📖 Step 7: Testing EPUB upload...")
        epub_content = b"PK\x03\x04\x14\x00\x00\x00\x08\x00"  # Basic EPUB header
        epub_success, epub_response = self.test_upload_book_file(book_id, epub_content, "test_book.epub")
        
        if epub_success:
            print("✅ EPUB upload successful")
        else:
            print("⚠️ EPUB upload failed (may be expected)")
        
        # Step 8: Test invalid file format
        print("\n❌ Step 8: Testing invalid file format...")
        invalid_success, invalid_response = self.test_upload_invalid_file_format(book_id)
        
        if invalid_success:
            print("✅ Invalid file format correctly rejected")
        else:
            print("⚠️ Invalid file format not properly rejected")
        
        print("\n🎯 DIGITAL BOOK FLOW TEST COMPLETED")
        self.log_test("Complete Digital Book Flow", True, "All steps completed successfully")
        return True

    def test_unauthorized_access(self):
        """Test accessing protected endpoints without authentication"""
        # Save current token
        saved_token = self.token
        self.token = None
        
        # Test protected endpoints (FastAPI HTTPBearer returns 403, not 401)
        success1, _ = self.run_test(
            "Unauthorized Access to /auth/me",
            "GET",
            "auth/me",
            403
        )
        
        success2, _ = self.run_test(
            "Unauthorized Access to Reserve Book",
            "POST",
            "loans/reserve",
            403,
            data={"book_id": "test-book-id"}
        )
        
        success3, _ = self.run_test(
            "Unauthorized Access to Download Book",
            "POST",
            "books/test-book-id/download",
            403
        )
        
        success4, _ = self.run_test(
            "Unauthorized Access to Serve Book File",
            "GET",
            "books/test-book-id/file",
            403
        )
        
        # Restore token
        self.token = saved_token
        
        return success1 and success2 and success3 and success4

    def create_test_books(self, school_id=None):
        """Create test books for testing catalog endpoints"""
        books_created = []
        
        # If no school_id provided, try to get it from current user
        if not school_id:
            success, user_info = self.test_get_current_user()
            if success and user_info and user_info.get('school_id'):
                school_id = user_info['school_id']
            else:
                print("⚠️ Warning: No school_id available for book creation")
                return books_created
        
        # Create a physical book
        physical_book_data = {
            "title": "Livre Physique Test",
            "authors": ["Auteur Physique"],
            "isbn": "978-2-111111-11-1",
            "description": "Un livre physique pour tester les réservations",
            "categories": ["Fiction", "Test"],
            "language": "fr",
            "format": "physical",
            "price": 12.50,
            "school_id": school_id,
            "physical_copies": 2
        }
        
        success, response = self.run_test(
            "Create Physical Test Book",
            "POST",
            "books",
            200,
            data=physical_book_data
        )
        
        if success and response:
            books_created.append({"type": "physical", "data": response})
        
        # Create a digital book
        digital_book_data = {
            "title": "Livre Numérique Test",
            "authors": ["Auteur Numérique"],
            "isbn": "978-2-222222-22-2",
            "description": "Un livre numérique pour tester les téléchargements",
            "categories": ["Science", "Test"],
            "language": "fr",
            "format": "digital",
            "price": 0.0,
            "school_id": school_id,
            "physical_copies": 0
        }
        
        success, response = self.run_test(
            "Create Digital Test Book",
            "POST",
            "books",
            200,
            data=digital_book_data
        )
        
        if success and response:
            books_created.append({"type": "digital", "data": response})
        
        # Create a book with both formats
        both_book_data = {
            "title": "Livre Mixte Test",
            "authors": ["Auteur Mixte"],
            "isbn": "978-2-333333-33-3",
            "description": "Un livre disponible en physique et numérique",
            "categories": ["Histoire", "Test"],
            "language": "fr",
            "format": "both",
            "price": 8.99,
            "school_id": school_id,
            "physical_copies": 1
        }
        
        success, response = self.run_test(
            "Create Mixed Format Test Book",
            "POST",
            "books",
            200,
            data=both_book_data
        )
        
        if success and response:
            books_created.append({"type": "both", "data": response})
        
        return books_created

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

        # Test 4: School Registration (no auth required)
        print("\n🏫 Testing School Registration...")
        self.token = None  # Clear token for school registration
        school_success, school_data = self.test_school_registration()

        # Test 5: School Admin Login (use the admin created during school registration)
        school_admin_success = False
        test_books = []
        if school_success and school_data:
            print("\n🎓 Testing School Admin Login...")
            school_info, school_creation_data = school_data
            school_admin_success, school_admin_info = self.test_user_login(
                school_creation_data['admin_email'], 
                school_creation_data['admin_password']
            )
            
            if school_admin_success:
                # Test 6: Dashboard stats as school admin
                print("\n📊 Testing Dashboard Stats (School Admin)...")
                self.test_dashboard_stats()
                
                # Test 7: Create test books for catalog testing
                print("\n📚 Creating Test Books for Catalog Interface...")
                test_books = self.create_test_books()

        # Test 8: Get books (public endpoint)
        print("\n📖 Testing Get Books List...")
        self.test_get_books()

        # Test 9: Test specific book retrieval
        if test_books:
            print("\n📖 Testing Get Book by ID...")
            for book in test_books:
                self.test_get_book_by_id(book['data']['id'])
        
        # Test 10: Test invalid book ID
        print("\n❌ Testing Get Book by Invalid ID...")
        self.test_get_book_by_invalid_id()

        # Test 11: Test unauthorized access
        print("\n🚫 Testing Unauthorized Access...")
        self.test_unauthorized_access()

        # Test 12: Test file upload functionality (CRITICAL PRIORITY)
        if school_admin_success and school_admin_info:
            print("\n🎯 PRIORITY TEST: File Upload Functionality...")
            self.test_complete_digital_book_flow()

        # Test 13-17: Test catalog interface endpoints with authentication
        if user_success and test_user:
            print("\n🔐 Re-authenticating test user for catalog tests...")
            login_success, user_info = self.test_user_login(test_user['email'], test_user['password'])
            
            if login_success and test_books:
                print("\n📚 Testing Catalog Interface Endpoints...")
                
                # Test book reservation (physical books)
                physical_books = [book for book in test_books if book['type'] in ['physical', 'both']]
                if physical_books:
                    print("\n📋 Testing Book Reservation...")
                    self.test_reserve_physical_book(physical_books[0]['data']['id'])
                
                # Test digital book download
                digital_books = [book for book in test_books if book['type'] in ['digital', 'both']]
                if digital_books:
                    print("\n💾 Testing Digital Book Download...")
                    self.test_download_digital_book(digital_books[0]['data']['id'])
                    
                    print("\n📁 Testing Book File Serving...")
                    self.test_serve_book_file(digital_books[0]['data']['id'])
                
                # Test error cases
                print("\n❌ Testing Error Cases...")
                self.test_reserve_nonexistent_book()
                self.test_reserve_without_book_id()
                self.test_download_nonexistent_book()
                self.test_serve_nonexistent_book_file()

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