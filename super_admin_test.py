import requests
import sys
import json
from datetime import datetime, timedelta

class SuperAdminTester:
    def __init__(self, base_url="https://libmanageduc.preview.emergentagent.com"):
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

    def create_super_admin(self):
        """Create a super admin user"""
        super_admin_data = {
            "email": "superadmin@schoollibrary.com",
            "password": "admin123",
            "full_name": "Super Administrateur",
            "role": "super_admin"
        }
        
        success, response = self.run_test(
            "Create Super Admin",
            "POST",
            "auth/register",
            200,
            data=super_admin_data
        )
        
        return success, super_admin_data if success else None

    def login_super_admin(self, email="superadmin@schoollibrary.com", password="admin123"):
        """Login as super admin"""
        success, response = self.run_test(
            "Super Admin Login",
            "POST",
            "auth/login",
            200,
            data={"email": email, "password": password}
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            return True, response['user']
        return False, None

    def test_get_all_schools(self):
        """Test getting all schools (super admin can see all)"""
        success, response = self.run_test(
            "Get All Schools (Super Admin)",
            "GET",
            "schools",
            200
        )
        return success, response if success else None

    def test_update_school_status(self, school_id, status):
        """Test updating school status"""
        success, response = self.run_test(
            f"Update School Status to {status}",
            "PUT",
            f"schools/{school_id}/status",
            200,
            data=status  # Send status as string directly
        )
        return success, response if success else None

    def test_super_admin_dashboard(self):
        """Test super admin dashboard stats"""
        success, response = self.run_test(
            "Super Admin Dashboard Stats",
            "GET",
            "dashboard/stats",
            200
        )
        return success, response if success else None

    def create_test_school(self):
        """Create a test school for status testing"""
        timestamp = datetime.now().strftime('%H%M%S')
        school_data = {
            "name": f"École Test Status {timestamp}",
            "address": "456 Avenue de Test, 75002 Paris",
            "country": "France",
            "description": "École pour tester les changements de statut",
            "admin_email": f"admin.status.{timestamp}@ecole-test.fr",
            "admin_name": f"Admin Status {timestamp}",
            "admin_password": "statuspass123"
        }
        
        # Clear token for school registration (no auth required)
        saved_token = self.token
        self.token = None
        
        success, response = self.run_test(
            "Create Test School for Status Testing",
            "POST",
            "schools",
            200,
            data=school_data
        )
        
        # Restore token
        self.token = saved_token
        
        return success, (response, school_data) if success else None

    def test_non_super_admin_school_status_update(self, school_id):
        """Test that non-super admin cannot update school status"""
        # Create a regular user
        regular_user_data = {
            "email": f"regular_{datetime.now().strftime('%H%M%S')}@test.com",
            "password": "regular123",
            "full_name": "Regular User",
            "role": "user"
        }
        
        # Clear token for registration
        saved_token = self.token
        self.token = None
        
        # Register regular user
        success, _ = self.run_test(
            "Create Regular User",
            "POST",
            "auth/register",
            200,
            data=regular_user_data
        )
        
        if not success:
            self.token = saved_token
            return False
        
        # Login as regular user
        success, response = self.run_test(
            "Login Regular User",
            "POST",
            "auth/login",
            200,
            data={"email": regular_user_data["email"], "password": regular_user_data["password"]}
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            
            # Try to update school status (should fail with 403)
            success, _ = self.run_test(
                "Regular User Try Update School Status (Should Fail)",
                "PUT",
                f"schools/{school_id}/status",
                403,
                data="approved"
            )
            
            # Restore super admin token
            self.token = saved_token
            return success
        
        # Restore token if login failed
        self.token = saved_token
        return False

    def run_super_admin_tests(self):
        """Run all super admin tests"""
        print("🚀 Starting Super Admin API Tests")
        print("=" * 50)

        # Test 1: Create super admin
        print("\n👑 Creating Super Admin...")
        admin_success, admin_data = self.create_super_admin()
        
        if not admin_success:
            # Try to login with existing super admin
            print("\n👑 Trying to login with existing Super Admin...")
            admin_success, admin_info = self.login_super_admin()
        else:
            # Login with newly created super admin
            print("\n🔐 Logging in as Super Admin...")
            admin_success, admin_info = self.login_super_admin(admin_data['email'], admin_data['password'])

        if not admin_success:
            print("❌ Cannot proceed without super admin access")
            return False

        # Test 2: Super admin dashboard
        print("\n📊 Testing Super Admin Dashboard...")
        self.test_super_admin_dashboard()

        # Test 3: Get all schools
        print("\n🏫 Testing Get All Schools (Super Admin View)...")
        schools_success, schools = self.test_get_all_schools()

        # Test 4: Create test school for status testing
        print("\n🏫 Creating Test School for Status Testing...")
        school_success, school_data = self.create_test_school()

        if school_success and school_data:
            school_info, school_creation_data = school_data
            school_id = school_info['id']
            
            # Test 5: Update school status to approved
            print("\n✅ Testing School Status Update: PENDING → APPROVED...")
            self.test_update_school_status(school_id, "approved")
            
            # Test 6: Update school status to rejected
            print("\n❌ Testing School Status Update: APPROVED → REJECTED...")
            self.test_update_school_status(school_id, "rejected")
            
            # Test 7: Update school status back to pending
            print("\n⏳ Testing School Status Update: REJECTED → PENDING...")
            self.test_update_school_status(school_id, "pending")
            
            # Test 8: Test non-super admin cannot update status
            print("\n🚫 Testing Non-Super Admin Cannot Update School Status...")
            self.test_non_super_admin_school_status_update(school_id)

        # Test 9: Verify schools list shows all statuses for super admin
        print("\n🏫 Verifying Super Admin Can See All School Statuses...")
        self.test_get_all_schools()

        # Print final results
        print("\n" + "=" * 50)
        print("📊 SUPER ADMIN TEST RESULTS")
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
    tester = SuperAdminTester()
    success = tester.run_super_admin_tests()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())