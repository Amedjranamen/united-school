#!/usr/bin/env python3
"""
Focused test for the new loan workflow with admin validation
"""
import requests
import json
from datetime import datetime

class FocusedLoanTester:
    def __init__(self, base_url="https://biblioplus.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.user_token = None
        self.admin_token = None
        self.test_results = []

    def log_result(self, test_name, success, details=""):
        """Log test result"""
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        
        self.test_results.append({
            "name": test_name,
            "success": success,
            "details": details
        })

    def make_request(self, method, endpoint, data=None, token=None):
        """Make API request"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=10)
            
            return response.status_code, response.json() if response.content else {}
        except Exception as e:
            return 500, {"error": str(e)}

    def test_authentication(self):
        """Test authentication system"""
        print("\n🔐 TESTING AUTHENTICATION SYSTEM")
        print("=" * 40)
        
        # Test 1: Register a new user
        timestamp = datetime.now().strftime('%H%M%S')
        user_data = {
            "email": f"testuser_{timestamp}@test.com",
            "password": "testpass123",
            "full_name": "Test User Loan",
            "role": "user"
        }
        
        status, response = self.make_request('POST', 'auth/register', user_data)
        if status == 200:
            self.log_result("User Registration", True)
            
            # Test 2: Login with the new user
            login_data = {"email": user_data["email"], "password": user_data["password"]}
            status, response = self.make_request('POST', 'auth/login', login_data)
            
            if status == 200 and 'access_token' in response:
                self.user_token = response['access_token']
                self.log_result("User Login", True)
                return True, user_data
            else:
                self.log_result("User Login", False, f"Status: {status}, Response: {response}")
                return False, None
        else:
            self.log_result("User Registration", False, f"Status: {status}, Response: {response}")
            return False, None

    def test_admin_authentication(self):
        """Test admin authentication"""
        print("\n🎓 TESTING ADMIN AUTHENTICATION")
        print("=" * 35)
        
        # Try to login as super admin
        admin_credentials = [
            {"email": "superadmin@schoollibrary.com", "password": "admin123"},
            {"email": "marie.dupont@ecole-arts.fr", "password": "marie123"}
        ]
        
        for creds in admin_credentials:
            status, response = self.make_request('POST', 'auth/login', creds)
            if status == 200 and 'access_token' in response:
                self.admin_token = response['access_token']
                self.log_result(f"Admin Login ({creds['email']})", True)
                return True, response['user']
        
        # If no existing admin works, create a school with admin
        timestamp = datetime.now().strftime('%H%M%S')
        school_data = {
            "name": f"École Test Loan {timestamp}",
            "address": "123 Rue Test, Paris",
            "country": "France",
            "admin_email": f"admin.loan.{timestamp}@test.fr",
            "admin_name": f"Admin Loan {timestamp}",
            "admin_password": "adminpass123"
        }
        
        status, response = self.make_request('POST', 'schools', school_data)
        if status == 200:
            self.log_result("School Registration", True)
            
            # Login as the new school admin
            admin_login = {
                "email": school_data["admin_email"],
                "password": school_data["admin_password"]
            }
            
            status, response = self.make_request('POST', 'auth/login', admin_login)
            if status == 200 and 'access_token' in response:
                self.admin_token = response['access_token']
                self.log_result("New School Admin Login", True)
                return True, response['user']
        
        self.log_result("Admin Authentication", False, "No admin credentials worked")
        return False, None

    def test_loan_workflow(self):
        """Test the complete loan workflow"""
        print("\n📚 TESTING COMPLETE LOAN WORKFLOW")
        print("=" * 40)
        
        if not self.user_token or not self.admin_token:
            self.log_result("Loan Workflow", False, "Missing authentication tokens")
            return False
        
        # Step 1: Admin creates a physical book
        book_data = {
            "title": "Livre Test Workflow Complet",
            "authors": ["Auteur Test"],
            "isbn": "978-2-777777-77-7",
            "description": "Livre pour tester le workflow d'emprunt complet",
            "categories": ["Test"],
            "language": "fr",
            "format": "physical",
            "price": 15.0,
            "school_id": "test-school-id",
            "physical_copies": 2
        }
        
        status, response = self.make_request('POST', 'books', book_data, self.admin_token)
        if status != 200:
            self.log_result("Create Test Book", False, f"Status: {status}, Response: {response}")
            return False
        
        book_id = response['id']
        self.log_result("Create Test Book", True, f"Book ID: {book_id}")
        
        # Step 2: User requests loan
        status, response = self.make_request('POST', 'loans/request', {"book_id": book_id}, self.user_token)
        if status != 200:
            self.log_result("Request Loan", False, f"Status: {status}, Response: {response}")
            return False
        
        loan_id = response.get('loan_id')
        if not loan_id:
            self.log_result("Request Loan", False, "No loan_id in response")
            return False
        
        self.log_result("Request Loan", True, f"Loan ID: {loan_id}, Status: {response.get('status')}")
        
        # Step 3: Verify loan is pending_approval
        status, response = self.make_request('GET', 'loans/my', None, self.user_token)
        if status == 200:
            loan_found = False
            for loan in response:
                if loan['id'] == loan_id:
                    if loan['status'] == 'pending_approval':
                        self.log_result("Verify Pending Status", True)
                        loan_found = True
                    else:
                        self.log_result("Verify Pending Status", False, f"Expected pending_approval, got {loan['status']}")
                        return False
                    break
            
            if not loan_found:
                self.log_result("Verify Pending Status", False, "Loan not found in user's loans")
                return False
        else:
            self.log_result("Verify Pending Status", False, f"Failed to get user loans: {status}")
            return False
        
        # Step 4: Admin approves loan
        approval_data = {
            "status": "approved",
            "admin_notes": "Demande approuvée pour test"
        }
        
        status, response = self.make_request('PUT', f'loans/{loan_id}/status', approval_data, self.admin_token)
        if status == 200:
            self.log_result("Admin Approve Loan", True)
        else:
            self.log_result("Admin Approve Loan", False, f"Status: {status}, Response: {response}")
            return False
        
        # Step 5: Admin marks as borrowed
        borrowed_data = {
            "status": "borrowed",
            "admin_notes": "Livre retiré par l'utilisateur"
        }
        
        status, response = self.make_request('PUT', f'loans/{loan_id}/status', borrowed_data, self.admin_token)
        if status == 200:
            self.log_result("Mark as Borrowed", True)
        else:
            self.log_result("Mark as Borrowed", False, f"Status: {status}, Response: {response}")
            return False
        
        # Step 6: User returns book
        return_data = {
            "status": "returned",
            "admin_notes": "Livre rendu en bon état"
        }
        
        status, response = self.make_request('PUT', f'loans/{loan_id}/status', return_data, self.user_token)
        if status == 200:
            self.log_result("User Return Book", True)
        else:
            self.log_result("User Return Book", False, f"Status: {status}, Response: {response}")
            return False
        
        # Step 7: Admin completes workflow
        complete_data = {
            "status": "completed",
            "admin_notes": "Retour validé, processus terminé"
        }
        
        status, response = self.make_request('PUT', f'loans/{loan_id}/status', complete_data, self.admin_token)
        if status == 200:
            self.log_result("Admin Complete Workflow", True)
        else:
            self.log_result("Admin Complete Workflow", False, f"Status: {status}, Response: {response}")
            return False
        
        # Step 8: Verify final status
        status, response = self.make_request('GET', 'loans', None, self.admin_token)
        if status == 200:
            for loan in response:
                if loan['id'] == loan_id:
                    if loan['status'] == 'completed':
                        self.log_result("Verify Final Status", True, "Workflow completed successfully")
                        return True
                    else:
                        self.log_result("Verify Final Status", False, f"Expected completed, got {loan['status']}")
                        return False
        
        self.log_result("Verify Final Status", False, "Could not verify final status")
        return False

    def test_digital_book_download(self):
        """Test digital book download functionality"""
        print("\n💾 TESTING DIGITAL BOOK DOWNLOAD")
        print("=" * 35)
        
        if not self.admin_token:
            self.log_result("Digital Book Test", False, "No admin token")
            return False
        
        # Create a digital book
        book_data = {
            "title": "Livre Numérique Test Download",
            "authors": ["Auteur Numérique"],
            "isbn": "978-2-888888-88-8",
            "description": "Livre numérique pour tester le téléchargement",
            "categories": ["Test", "Numérique"],
            "language": "fr",
            "format": "digital",
            "price": 0.0,
            "school_id": "test-school-id",
            "physical_copies": 0
        }
        
        status, response = self.make_request('POST', 'books', book_data, self.admin_token)
        if status != 200:
            self.log_result("Create Digital Book", False, f"Status: {status}")
            return False
        
        book_id = response['id']
        self.log_result("Create Digital Book", True, f"Book ID: {book_id}")
        
        # Try to download without file (should fail)
        status, response = self.make_request('POST', f'books/{book_id}/download', None, self.user_token)
        if status == 404 and 'Fichier non disponible' in response.get('detail', ''):
            self.log_result("Download Without File", True, "Correctly rejected - no file uploaded")
        else:
            self.log_result("Download Without File", False, f"Expected 404, got {status}")
        
        return True

    def run_all_tests(self):
        """Run all focused tests"""
        print("🚀 FOCUSED LOAN WORKFLOW TESTS")
        print("=" * 50)
        
        # Test authentication
        auth_success, user_data = self.test_authentication()
        admin_success, admin_data = self.test_admin_authentication()
        
        if auth_success and admin_success:
            # Test loan workflow
            self.test_loan_workflow()
        
        # Test digital book functionality
        self.test_digital_book_download()
        
        # Print results
        print("\n" + "=" * 50)
        print("📊 FOCUSED TEST RESULTS")
        print("=" * 50)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        print(f"Tests passed: {passed}/{total}")
        print(f"Success rate: {(passed/total)*100:.1f}%")
        
        failed_tests = [test for test in self.test_results if not test['success']]
        if failed_tests:
            print("\n❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"   - {test['name']}: {test['details']}")
        
        return passed == total

def main():
    tester = FocusedLoanTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())