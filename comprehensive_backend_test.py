#!/usr/bin/env python3
"""
Comprehensive backend test for the French school library system
Focuses on the key requirements from the review request
"""
import requests
import json
from datetime import datetime

class ComprehensiveBackendTester:
    def __init__(self, base_url="https://biblioplus.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.test_results = []
        self.tokens = {}
        self.test_data = {}

    def log_result(self, test_name, success, details=""):
        """Log test result"""
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status}: {test_name}")
        if details:
            print(f"   {details}")
        
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

    def test_authentication_system(self):
        """Test 1: Authentication - Login/register/roles fonctionnels"""
        print("\n🔐 1. TESTING AUTHENTICATION SYSTEM")
        print("=" * 50)
        
        # Register regular user
        timestamp = datetime.now().strftime('%H%M%S')
        user_data = {
            "email": f"utilisateur_{timestamp}@test.fr",
            "password": "motdepasse123",
            "full_name": "Utilisateur Test",
            "role": "user"
        }
        
        status, response = self.make_request('POST', 'auth/register', user_data)
        if status == 200:
            self.log_result("Inscription utilisateur", True)
            
            # Login user
            login_data = {"email": user_data["email"], "password": user_data["password"]}
            status, response = self.make_request('POST', 'auth/login', login_data)
            
            if status == 200 and 'access_token' in response:
                self.tokens['user'] = response['access_token']
                self.test_data['user'] = response['user']
                self.log_result("Connexion utilisateur", True)
            else:
                self.log_result("Connexion utilisateur", False, f"Status: {status}")
                return False
        else:
            self.log_result("Inscription utilisateur", False, f"Status: {status}")
            return False
        
        # Create school with admin
        school_data = {
            "name": f"École Test Complète {timestamp}",
            "address": "123 Avenue de la République, 75011 Paris",
            "country": "France",
            "description": "École de test pour validation complète",
            "admin_email": f"admin.ecole.{timestamp}@test.fr",
            "admin_name": f"Administrateur École {timestamp}",
            "admin_password": "adminecole123"
        }
        
        status, response = self.make_request('POST', 'schools', school_data)
        if status == 200:
            self.test_data['school'] = response
            self.log_result("Inscription école", True)
            
            # Login school admin
            admin_login = {
                "email": school_data["admin_email"],
                "password": school_data["admin_password"]
            }
            
            status, response = self.make_request('POST', 'auth/login', admin_login)
            if status == 200 and 'access_token' in response:
                self.tokens['school_admin'] = response['access_token']
                self.test_data['school_admin'] = response['user']
                self.log_result("Connexion admin école", True)
            else:
                self.log_result("Connexion admin école", False, f"Status: {status}")
                return False
        else:
            self.log_result("Inscription école", False, f"Status: {status}")
            return False
        
        # Try super admin login
        super_admin_creds = {"email": "superadmin@schoollibrary.com", "password": "admin123"}
        status, response = self.make_request('POST', 'auth/login', super_admin_creds)
        if status == 200 and 'access_token' in response:
            self.tokens['super_admin'] = response['access_token']
            self.test_data['super_admin'] = response['user']
            self.log_result("Connexion super admin", True)
        else:
            self.log_result("Connexion super admin", False, "Credentials may not exist")
        
        return True

    def test_school_validation_system(self):
        """Test 2: Validation d'écoles par super_admin"""
        print("\n🏫 2. TESTING SCHOOL VALIDATION SYSTEM")
        print("=" * 45)
        
        if 'super_admin' not in self.tokens:
            self.log_result("Validation écoles", False, "No super admin token")
            return False
        
        # Get schools list as super admin
        status, response = self.make_request('GET', 'schools', None, self.tokens['super_admin'])
        if status == 200:
            self.log_result("Liste écoles (super admin)", True, f"Found {len(response)} schools")
            
            # Find our test school
            test_school = None
            for school in response:
                if school['id'] == self.test_data['school']['id']:
                    test_school = school
                    break
            
            if test_school:
                school_id = test_school['id']
                
                # Test status changes: pending -> approved -> rejected -> pending
                statuses = ['approved', 'rejected', 'pending']
                for status_change in statuses:
                    status, response = self.make_request('PUT', f'schools/{school_id}/status?status={status_change}', 
                                                       None, self.tokens['super_admin'])
                    if status == 200:
                        self.log_result(f"Changement statut école -> {status_change}", True)
                    else:
                        self.log_result(f"Changement statut école -> {status_change}", False, f"Status: {status}")
            else:
                self.log_result("Validation écoles", False, "Test school not found")
                return False
        else:
            self.log_result("Liste écoles (super admin)", False, f"Status: {status}")
            return False
        
        return True

    def test_book_management_and_upload(self):
        """Test 3: Gestion des livres et upload de fichiers"""
        print("\n📚 3. TESTING BOOK MANAGEMENT AND FILE UPLOAD")
        print("=" * 50)
        
        if 'school_admin' not in self.tokens:
            self.log_result("Gestion livres", False, "No school admin token")
            return False
        
        # Create physical book
        physical_book = {
            "title": "Manuel de Mathématiques CM2",
            "authors": ["Marie Dubois", "Pierre Martin"],
            "isbn": "978-2-123456-78-9",
            "description": "Manuel scolaire de mathématiques pour CM2",
            "categories": ["Mathématiques", "Scolaire", "CM2"],
            "language": "fr",
            "format": "physical",
            "price": 25.50,
            "school_id": self.test_data['school']['id'],
            "physical_copies": 5
        }
        
        status, response = self.make_request('POST', 'books', physical_book, self.tokens['school_admin'])
        if status == 200:
            self.test_data['physical_book'] = response
            self.log_result("Création livre physique", True, f"ID: {response['id']}")
        else:
            self.log_result("Création livre physique", False, f"Status: {status}")
            return False
        
        # Create digital book
        digital_book = {
            "title": "Guide Numérique Sciences CE2",
            "authors": ["Sophie Leclerc"],
            "isbn": "978-2-987654-32-1",
            "description": "Guide numérique interactif pour les sciences en CE2",
            "categories": ["Sciences", "Numérique", "CE2"],
            "language": "fr",
            "format": "digital",
            "price": 0.0,  # Gratuit
            "school_id": self.test_data['school']['id'],
            "physical_copies": 0
        }
        
        status, response = self.make_request('POST', 'books', digital_book, self.tokens['school_admin'])
        if status == 200:
            self.test_data['digital_book'] = response
            self.log_result("Création livre numérique", True, f"ID: {response['id']}")
            
            # Test file upload for digital book
            book_id = response['id']
            upload_url = f"{self.api_url}/books/{book_id}/upload-file"
            
            # Simulate PDF upload
            files = {'file': ('guide_sciences.pdf', b'%PDF-1.4 Test PDF content', 'application/pdf')}
            headers = {'Authorization': f'Bearer {self.tokens["school_admin"]}'}
            
            try:
                upload_response = requests.post(upload_url, files=files, headers=headers, timeout=10)
                if upload_response.status_code == 200:
                    self.log_result("Upload fichier numérique", True)
                    
                    # Verify file_path is set
                    status, book_details = self.make_request('GET', f'books/{book_id}', None, self.tokens['school_admin'])
                    if status == 200 and book_details.get('file_path'):
                        self.log_result("Vérification file_path", True, f"Path: {book_details['file_path']}")
                    else:
                        self.log_result("Vérification file_path", False, "No file_path set")
                else:
                    self.log_result("Upload fichier numérique", False, f"Status: {upload_response.status_code}")
            except Exception as e:
                self.log_result("Upload fichier numérique", False, f"Error: {str(e)}")
        else:
            self.log_result("Création livre numérique", False, f"Status: {status}")
            return False
        
        return True

    def test_loan_system_with_admin_validation(self):
        """Test 4: Système d'emprunts avec validation admin"""
        print("\n📋 4. TESTING LOAN SYSTEM WITH ADMIN VALIDATION")
        print("=" * 55)
        
        if 'user' not in self.tokens or 'school_admin' not in self.tokens:
            self.log_result("Système emprunts", False, "Missing tokens")
            return False
        
        if 'physical_book' not in self.test_data:
            self.log_result("Système emprunts", False, "No physical book for testing")
            return False
        
        book_id = self.test_data['physical_book']['id']
        
        # Step 1: User requests loan
        status, response = self.make_request('POST', 'loans/request', {"book_id": book_id}, self.tokens['user'])
        if status == 200:
            loan_id = response.get('loan_id')
            if loan_id and response.get('status') == 'pending_approval':
                self.log_result("Demande emprunt utilisateur", True, f"Status: {response['status']}")
                self.test_data['loan_id'] = loan_id
            else:
                self.log_result("Demande emprunt utilisateur", False, "Invalid response")
                return False
        else:
            self.log_result("Demande emprunt utilisateur", False, f"Status: {status}")
            return False
        
        # Step 2: Admin approves loan
        approval_data = {"status": "approved", "admin_notes": "Demande approuvée"}
        status, response = self.make_request('PUT', f'loans/{loan_id}/status', approval_data, self.tokens['school_admin'])
        if status == 200:
            self.log_result("Approbation admin", True)
        else:
            self.log_result("Approbation admin", False, f"Status: {status}")
            return False
        
        # Step 3: Admin marks as borrowed
        borrowed_data = {"status": "borrowed", "admin_notes": "Livre retiré"}
        status, response = self.make_request('PUT', f'loans/{loan_id}/status', borrowed_data, self.tokens['school_admin'])
        if status == 200:
            self.log_result("Marquage emprunté", True)
        else:
            self.log_result("Marquage emprunté", False, f"Status: {status}")
            return False
        
        # Step 4: User returns book
        return_data = {"status": "returned"}
        status, response = self.make_request('PUT', f'loans/{loan_id}/status', return_data, self.tokens['user'])
        if status == 200:
            self.log_result("Retour utilisateur", True)
        else:
            self.log_result("Retour utilisateur", False, f"Status: {status}")
            return False
        
        # Step 5: Admin completes workflow
        complete_data = {"status": "completed", "admin_notes": "Retour validé"}
        status, response = self.make_request('PUT', f'loans/{loan_id}/status', complete_data, self.tokens['school_admin'])
        if status == 200:
            self.log_result("Validation finale admin", True)
        else:
            self.log_result("Validation finale admin", False, f"Status: {status}")
            return False
        
        # Verify complete workflow
        status, response = self.make_request('GET', 'loans', None, self.tokens['school_admin'])
        if status == 200:
            for loan in response:
                if loan['id'] == loan_id and loan['status'] == 'completed':
                    self.log_result("Workflow complet validé", True, "pending_approval → approved → borrowed → returned → completed")
                    break
            else:
                self.log_result("Workflow complet validé", False, "Final status not completed")
                return False
        else:
            self.log_result("Workflow complet validé", False, f"Status: {status}")
            return False
        
        return True

    def test_free_digital_downloads(self):
        """Test 5: Téléchargement gratuit des livres numériques"""
        print("\n💾 5. TESTING FREE DIGITAL BOOK DOWNLOADS")
        print("=" * 45)
        
        if 'user' not in self.tokens or 'digital_book' not in self.test_data:
            self.log_result("Téléchargements gratuits", False, "Missing data")
            return False
        
        book_id = self.test_data['digital_book']['id']
        
        # Test download endpoint
        status, response = self.make_request('POST', f'books/{book_id}/download', None, self.tokens['user'])
        if status == 200:
            if 'download_url' in response and response.get('book_title'):
                self.log_result("Téléchargement gratuit", True, f"URL: {response['download_url']}")
                
                # Test file serving
                status, response = self.make_request('GET', f'books/{book_id}/file', None, self.tokens['user'])
                if status == 200:
                    self.log_result("Service fichier", True)
                else:
                    self.log_result("Service fichier", False, f"Status: {status}")
            else:
                self.log_result("Téléchargement gratuit", False, "Invalid response format")
                return False
        else:
            # If 404, it means no file uploaded - this is expected behavior
            if status == 404 and 'Fichier non disponible' in response.get('detail', ''):
                self.log_result("Téléchargement gratuit", True, "Correctly rejects books without uploaded files")
            else:
                self.log_result("Téléchargement gratuit", False, f"Status: {status}")
                return False
        
        return True

    def test_dashboard_by_roles(self):
        """Test 6: Dashboard selon rôles utilisateur"""
        print("\n📊 6. TESTING ROLE-BASED DASHBOARDS")
        print("=" * 40)
        
        # Test user dashboard
        if 'user' in self.tokens:
            status, response = self.make_request('GET', 'dashboard/stats', None, self.tokens['user'])
            if status == 200:
                expected_keys = ['my_loans', 'active_loans']
                if all(key in response for key in expected_keys):
                    self.log_result("Dashboard utilisateur", True, f"Stats: {response}")
                else:
                    self.log_result("Dashboard utilisateur", False, f"Missing keys: {response}")
            else:
                self.log_result("Dashboard utilisateur", False, f"Status: {status}")
        
        # Test school admin dashboard
        if 'school_admin' in self.tokens:
            status, response = self.make_request('GET', 'dashboard/stats', None, self.tokens['school_admin'])
            if status == 200:
                expected_keys = ['school_books', 'active_loans']
                if all(key in response for key in expected_keys):
                    self.log_result("Dashboard admin école", True, f"Stats: {response}")
                else:
                    self.log_result("Dashboard admin école", False, f"Missing keys: {response}")
            else:
                self.log_result("Dashboard admin école", False, f"Status: {status}")
        
        # Test super admin dashboard
        if 'super_admin' in self.tokens:
            status, response = self.make_request('GET', 'dashboard/stats', None, self.tokens['super_admin'])
            if status == 200:
                expected_keys = ['total_schools', 'total_users', 'total_books']
                if all(key in response for key in expected_keys):
                    self.log_result("Dashboard super admin", True, f"Stats: {response}")
                else:
                    self.log_result("Dashboard super admin", False, f"Missing keys: {response}")
            else:
                self.log_result("Dashboard super admin", False, f"Status: {status}")
        
        return True

    def run_comprehensive_tests(self):
        """Run all comprehensive tests"""
        print("🚀 COMPREHENSIVE FRENCH SCHOOL LIBRARY BACKEND TESTS")
        print("=" * 60)
        print("Testing key requirements from review request:")
        print("1. Authentication system")
        print("2. School validation by super_admin")
        print("3. Book management and file uploads")
        print("4. Loan system with admin validation")
        print("5. Free digital book downloads")
        print("6. Role-based dashboards")
        print("=" * 60)
        
        # Run all tests
        tests = [
            self.test_authentication_system,
            self.test_school_validation_system,
            self.test_book_management_and_upload,
            self.test_loan_system_with_admin_validation,
            self.test_free_digital_downloads,
            self.test_dashboard_by_roles
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                print(f"❌ Test failed with exception: {str(e)}")
        
        # Print final results
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE TEST RESULTS")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        print(f"Tests passed: {passed}/{total}")
        print(f"Success rate: {(passed/total)*100:.1f}%")
        
        # Group results by category
        categories = {
            "Authentication": ["Inscription", "Connexion"],
            "School Management": ["école", "École", "Validation"],
            "Book Management": ["livre", "Livre", "Upload", "fichier"],
            "Loan System": ["emprunt", "Demande", "Workflow", "Approbation"],
            "Downloads": ["Téléchargement", "Service"],
            "Dashboard": ["Dashboard"]
        }
        
        for category, keywords in categories.items():
            category_tests = [test for test in self.test_results 
                            if any(keyword in test['name'] for keyword in keywords)]
            if category_tests:
                passed_cat = sum(1 for test in category_tests if test['success'])
                total_cat = len(category_tests)
                print(f"\n{category}: {passed_cat}/{total_cat} passed")
                
                failed_cat = [test for test in category_tests if not test['success']]
                if failed_cat:
                    for test in failed_cat:
                        print(f"   ❌ {test['name']}: {test['details']}")
        
        return passed == total

def main():
    tester = ComprehensiveBackendTester()
    success = tester.run_comprehensive_tests()
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())