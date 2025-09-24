import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Link, Navigate, useLocation } from 'react-router-dom';
import axios from 'axios';
import './App.css';

// Import Shadcn components
import { Button } from './components/ui/button';
import { Input } from './components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from './components/ui/card';
import { Badge } from './components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from './components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './components/ui/select';
import { Textarea } from './components/ui/textarea';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from './components/ui/dropdown-menu';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from './components/ui/alert-dialog';
import { Label } from './components/ui/label';
import { Separator } from './components/ui/separator';
import { useToast } from './hooks/use-toast';
import { Toaster } from './components/ui/toaster';

// Icons
import { Search, Book, Users, Plus, Upload, Eye, Download, User, School, FileText, Calendar, CheckCircle, XCircle, Edit, Trash2, BookOpen, Filter, MoreHorizontal } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Authentication context
const AuthContext = React.createContext();

const useAuth = () => {
  const context = React.useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const verifyToken = async () => {
      if (token) {
        try {
          const response = await axios.get(`${API}/auth/me`, {
            headers: { Authorization: `Bearer ${token}` }
          });
          setUser(response.data);
        } catch (error) {
          localStorage.removeItem('token');
          setToken(null);
        }
      }
      setLoading(false);
    };

    verifyToken();
  }, [token]);

  const login = async (email, password) => {
    try {
      const response = await axios.post(`${API}/auth/login`, { email, password });
      const { access_token, user } = response.data;
      
      localStorage.setItem('token', access_token);
      setToken(access_token);
      setUser(user);
      
      return { success: true };
    } catch (error) {
      return { success: false, error: error.response?.data?.detail || 'Erreur de connexion' };
    }
  };

  const register = async (userData) => {
    try {
      const response = await axios.post(`${API}/auth/register`, userData);
      return { success: true, user: response.data };
    } catch (error) {
      return { success: false, error: error.response?.data?.detail || 'Erreur d\'inscription' };
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
  };

  const value = {
    user,
    token,
    login,
    register,
    logout,
    loading
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

// Protected Route component
const ProtectedRoute = ({ children, roles = [] }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600"></div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" />;
  }

  if (roles.length > 0 && !roles.includes(user.role)) {
    return <Navigate to="/dashboard" />;
  }

  return children;
};

// Header component
const Header = () => {
  const { user, logout } = useAuth();
  const location = useLocation();

  if (location.pathname === '/login' || location.pathname === '/register') {
    return null;
  }

  return (
    <header className="bg-white border-b border-emerald-100 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <Link to="/dashboard" className="flex items-center space-x-2">
            <Book className="h-8 w-8 text-emerald-600" />
            <span className="text-xl font-bold text-emerald-800">Bibliothèque Scolaire</span>
          </Link>

          {user && (
            <nav className="flex items-center space-x-6">
              <Link to="/dashboard" className="text-gray-700 hover:text-emerald-600 transition-colors">
                Tableau de bord
              </Link>
              <Link to="/catalogue" className="text-gray-700 hover:text-emerald-600 transition-colors">
                Catalogue
              </Link>
              {['school_admin', 'librarian', 'teacher'].includes(user.role) && (
                <Link to="/manage-books" className="text-gray-700 hover:text-emerald-600 transition-colors">
                  Gérer les livres
                </Link>
              )}
              {user.role === 'super_admin' && (
                <Link to="/admin" className="text-gray-700 hover:text-emerald-600 transition-colors">
                  Administration
                </Link>
              )}
              <div className="flex items-center space-x-3">
                <Badge variant="outline" className="bg-emerald-50 text-emerald-700">
                  {user.full_name}
                </Badge>
                <Button variant="ghost" size="sm" onClick={logout} data-testid="logout-button">
                  Déconnexion
                </Button>
              </div>
            </nav>
          )}
        </div>
      </div>
    </header>
  );
};

// Login component
const Login = () => {
  const [formData, setFormData] = useState({ email: '', password: '' });
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const { toast } = useToast();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    const result = await login(formData.email, formData.password);
    
    if (result.success) {
      toast({ title: "Connexion réussie", description: "Bienvenue !" });
    } else {
      toast({ 
        variant: "destructive",
        title: "Erreur de connexion", 
        description: result.error 
      });
    }
    
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-white to-orange-50 flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="flex justify-center mb-4">
            <Book className="h-12 w-12 text-emerald-600" />
          </div>
          <CardTitle className="text-2xl text-emerald-800">Connexion</CardTitle>
          <p className="text-gray-600">Accédez à votre bibliothèque scolaire</p>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({...formData, email: e.target.value})}
                required
                data-testid="email-input"
                className="focus:ring-emerald-500 focus:border-emerald-500"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Mot de passe</Label>
              <Input
                id="password"
                type="password"
                value={formData.password}
                onChange={(e) => setFormData({...formData, password: e.target.value})}
                required
                data-testid="password-input"
                className="focus:ring-emerald-500 focus:border-emerald-500"
              />
            </div>
            <Button 
              type="submit" 
              className="w-full bg-emerald-600 hover:bg-emerald-700" 
              disabled={loading}
              data-testid="login-submit"
            >
              {loading ? 'Connexion...' : 'Se connecter'}
            </Button>
          </form>
          
          <Separator className="my-6" />
          
          <div className="text-center space-y-2">
            <p className="text-sm text-gray-600">Pas encore de compte ?</p>
            <Link to="/register">
              <Button variant="outline" className="w-full border-emerald-200 hover:bg-emerald-50" data-testid="register-link">
                S'inscrire
              </Button>
            </Link>
            <Link to="/register-school">
              <Button variant="outline" className="w-full border-orange-200 hover:bg-orange-50 text-orange-700" data-testid="register-school-link">
                Inscrire une école
              </Button>
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

// Register component
const Register = () => {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    full_name: '',
    phone: '',
    role: 'user'
  });
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();
  const { toast } = useToast();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    const result = await register(formData);
    
    if (result.success) {
      toast({ 
        title: "Inscription réussie", 
        description: "Votre compte a été créé. Vous pouvez maintenant vous connecter." 
      });
      window.location.href = '/login';
    } else {
      toast({ 
        variant: "destructive",
        title: "Erreur d'inscription", 
        description: result.error 
      });
    }
    
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-white to-orange-50 flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="flex justify-center mb-4">
            <User className="h-12 w-12 text-emerald-600" />
          </div>
          <CardTitle className="text-2xl text-emerald-800">Inscription</CardTitle>
          <p className="text-gray-600">Créez votre compte utilisateur</p>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="full_name">Nom complet</Label>
              <Input
                id="full_name"
                value={formData.full_name}
                onChange={(e) => setFormData({...formData, full_name: e.target.value})}
                required
                data-testid="fullname-input"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({...formData, email: e.target.value})}
                required
                data-testid="email-input"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="phone">Téléphone (optionnel)</Label>
              <Input
                id="phone"
                value={formData.phone}
                onChange={(e) => setFormData({...formData, phone: e.target.value})}
                data-testid="phone-input"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Mot de passe</Label>
              <Input
                id="password"
                type="password"
                value={formData.password}
                onChange={(e) => setFormData({...formData, password: e.target.value})}
                required
                data-testid="password-input"
              />
            </div>
            <Button 
              type="submit" 
              className="w-full bg-emerald-600 hover:bg-emerald-700" 
              disabled={loading}
              data-testid="register-submit"
            >
              {loading ? 'Inscription...' : 'S\'inscrire'}
            </Button>
          </form>
          
          <Separator className="my-6" />
          
          <div className="text-center">
            <p className="text-sm text-gray-600">Déjà un compte ?</p>
            <Link to="/login">
              <Button variant="outline" className="w-full mt-2" data-testid="login-link">
                Se connecter
              </Button>
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

// School Registration component
const RegisterSchool = () => {
  const [formData, setFormData] = useState({
    name: '',
    address: '',
    country: 'France',
    description: '',
    admin_email: '',
    admin_name: '',
    admin_password: ''
  });
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      await axios.post(`${API}/schools`, formData);
      toast({ 
        title: "Demande envoyée", 
        description: "Votre demande d'inscription d'école a été envoyée. Elle sera examinée par un administrateur." 
      });
      window.location.href = '/login';
    } catch (error) {
      toast({ 
        variant: "destructive",
        title: "Erreur", 
        description: error.response?.data?.detail || 'Erreur lors de l\'inscription' 
      });
    }
    
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-white to-orange-50 flex items-center justify-center p-4">
      <Card className="w-full max-w-2xl">
        <CardHeader className="text-center">
          <div className="flex justify-center mb-4">
            <School className="h-12 w-12 text-emerald-600" />
          </div>
          <CardTitle className="text-2xl text-emerald-800">Inscription d'École</CardTitle>
          <p className="text-gray-600">Inscrivez votre établissement scolaire</p>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="name">Nom de l'école</Label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                  required
                  data-testid="school-name-input"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="country">Pays</Label>
                <Input
                  id="country"
                  value={formData.country}
                  onChange={(e) => setFormData({...formData, country: e.target.value})}
                  required
                  data-testid="country-input"
                />
              </div>
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="address">Adresse</Label>
              <Textarea
                id="address"
                value={formData.address}
                onChange={(e) => setFormData({...formData, address: e.target.value})}
                required
                data-testid="address-input"
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="description">Description (optionnel)</Label>
              <Textarea
                id="description"
                value={formData.description}
                onChange={(e) => setFormData({...formData, description: e.target.value})}
                placeholder="Présentez votre établissement..."
                data-testid="description-input"
              />
            </div>

            <Separator />
            
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-800">Informations de l'administrateur</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="admin_name">Nom de l'administrateur</Label>
                  <Input
                    id="admin_name"
                    value={formData.admin_name}
                    onChange={(e) => setFormData({...formData, admin_name: e.target.value})}
                    required
                    data-testid="admin-name-input"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="admin_email">Email de l'administrateur</Label>
                  <Input
                    id="admin_email"
                    type="email"
                    value={formData.admin_email}
                    onChange={(e) => setFormData({...formData, admin_email: e.target.value})}
                    required
                    data-testid="admin-email-input"
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="admin_password">Mot de passe de l'administrateur</Label>
                <Input
                  id="admin_password"
                  type="password"
                  value={formData.admin_password}
                  onChange={(e) => setFormData({...formData, admin_password: e.target.value})}
                  required
                  data-testid="admin-password-input"
                />
              </div>
            </div>
            
            <Button 
              type="submit" 
              className="w-full bg-emerald-600 hover:bg-emerald-700" 
              disabled={loading}
              data-testid="school-register-submit"
            >
              {loading ? 'Envoi en cours...' : 'Envoyer la demande'}
            </Button>
          </form>
          
          <Separator className="my-6" />
          
          <div className="text-center">
            <Link to="/login">
              <Button variant="outline" className="w-full" data-testid="back-to-login">
                Retour à la connexion
              </Button>
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

// Dashboard component
const Dashboard = () => {
  const { user, token } = useAuth();
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await axios.get(`${API}/dashboard/stats`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setStats(response.data);
      } catch (error) {
        console.error('Error fetching stats:', error);
      }
      setLoading(false);
    };

    fetchStats();
  }, [token]);

  const getRoleLabel = (role) => {
    const labels = {
      super_admin: 'Super Administrateur',
      school_admin: 'Administrateur d\'École',
      librarian: 'Bibliothécaire',
      teacher: 'Enseignant',
      user: 'Utilisateur'
    };
    return labels[role] || role;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600"></div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900" data-testid="dashboard-title">
          Tableau de bord
        </h1>
        <p className="text-gray-600 mt-2">
          Bienvenue, {user.full_name} ({getRoleLabel(user.role)})
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {user.role === 'super_admin' && (
          <>
            <Card data-testid="total-schools-card">
              <CardContent className="p-6">
                <div className="flex items-center">
                  <School className="h-8 w-8 text-emerald-600" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Écoles totales</p>
                    <p className="text-2xl font-bold text-gray-900">{stats.total_schools || 0}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card data-testid="pending-schools-card">
              <CardContent className="p-6">
                <div className="flex items-center">
                  <Calendar className="h-8 w-8 text-orange-600" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">En attente</p>
                    <p className="text-2xl font-bold text-gray-900">{stats.pending_schools || 0}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card data-testid="total-users-card">
              <CardContent className="p-6">
                <div className="flex items-center">
                  <Users className="h-8 w-8 text-blue-600" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Utilisateurs</p>
                    <p className="text-2xl font-bold text-gray-900">{stats.total_users || 0}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card data-testid="total-books-card">
              <CardContent className="p-6">
                <div className="flex items-center">
                  <Book className="h-8 w-8 text-green-600" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Livres</p>
                    <p className="text-2xl font-bold text-gray-900">{stats.total_books || 0}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </>
        )}

        {['school_admin', 'librarian'].includes(user.role) && (
          <>
            <Card data-testid="school-books-card">
              <CardContent className="p-6">
                <div className="flex items-center">
                  <Book className="h-8 w-8 text-emerald-600" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Livres de l'école</p>
                    <p className="text-2xl font-bold text-gray-900">{stats.school_books || 0}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card data-testid="active-loans-card">
              <CardContent className="p-6">
                <div className="flex items-center">
                  <FileText className="h-8 w-8 text-orange-600" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Emprunts actifs</p>
                    <p className="text-2xl font-bold text-gray-900">{stats.active_loans || 0}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card data-testid="total-copies-card">
              <CardContent className="p-6">
                <div className="flex items-center">
                  <Book className="h-8 w-8 text-blue-600" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Exemplaires</p>
                    <p className="text-2xl font-bold text-gray-900">{stats.total_copies || 0}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </>
        )}

        {user.role === 'user' && (
          <>
            <Card data-testid="my-loans-card">
              <CardContent className="p-6">
                <div className="flex items-center">
                  <Book className="h-8 w-8 text-emerald-600" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Mes emprunts</p>
                    <p className="text-2xl font-bold text-gray-900">{stats.my_loans || 0}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card data-testid="my-active-loans-card">
              <CardContent className="p-6">
                <div className="flex items-center">
                  <Calendar className="h-8 w-8 text-orange-600" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Emprunts actifs</p>
                    <p className="text-2xl font-bold text-gray-900">{stats.active_loans || 0}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Actions rapides</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              <Link to="/catalogue">
                <Button className="w-full h-24 bg-emerald-600 hover:bg-emerald-700" data-testid="browse-catalog-btn">
                  <div className="text-center">
                    <Search className="h-6 w-6 mx-auto mb-2" />
                    <span>Parcourir le catalogue</span>
                  </div>
                </Button>
              </Link>
              {['school_admin', 'librarian', 'teacher'].includes(user.role) && (
                <Link to="/manage-books">
                  <Button variant="outline" className="w-full h-24" data-testid="manage-books-btn">
                    <div className="text-center">
                      <Plus className="h-6 w-6 mx-auto mb-2" />
                      <span>Gérer les livres</span>
                    </div>
                  </Button>
                </Link>
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Informations</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="p-4 bg-emerald-50 rounded-lg">
                <h4 className="font-semibold text-emerald-800">Bienvenue!</h4>
                <p className="text-sm text-emerald-600 mt-1">
                  Explorez notre bibliothèque numérique et physique.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

function App() {
  return (
    <AuthProvider>
      <div className="App min-h-screen bg-gray-50">
        <BrowserRouter>
          <Header />
          <main>
            <Routes>
              <Route path="/" element={<Navigate to="/dashboard" />} />
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
              <Route path="/register-school" element={<RegisterSchool />} />
              <Route 
                path="/dashboard" 
                element={
                  <ProtectedRoute>
                    <Dashboard />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/catalogue" 
                element={
                  <ProtectedRoute>
                    <div className="max-w-7xl mx-auto px-4 py-8">
                      <h1 className="text-3xl font-bold mb-8 text-center">Catalogue (À venir)</h1>
                      <p className="text-center text-gray-600">
                        Le catalogue complet sera disponible dans la prochaine version.
                      </p>
                    </div>
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/manage-books" 
                element={
                  <ProtectedRoute roles={['school_admin', 'librarian', 'teacher']}>
                    <div className="max-w-7xl mx-auto px-4 py-8">
                      <h1 className="text-3xl font-bold mb-8 text-center">Gestion des livres (À venir)</h1>
                      <p className="text-center text-gray-600">
                        La gestion des livres sera disponible dans la prochaine version.
                      </p>
                    </div>
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/admin" 
                element={
                  <ProtectedRoute roles={['super_admin']}>
                    <div className="max-w-7xl mx-auto px-4 py-8">
                      <h1 className="text-3xl font-bold mb-8 text-center">Administration (À venir)</h1>
                      <p className="text-center text-gray-600">
                        Le panneau d'administration sera disponible dans la prochaine version.
                      </p>
                    </div>
                  </ProtectedRoute>
                } 
              />
            </Routes>
          </main>
          <Toaster />
        </BrowserRouter>
      </div>
    </AuthProvider>
  );
}

export default App;