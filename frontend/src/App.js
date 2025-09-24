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

// Manage Books component
const ManageBooks = () => {
  const { user, token } = useAuth();
  const { toast } = useToast();
  const [books, setBooks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [editingBook, setEditingBook] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterFormat, setFilterFormat] = useState('all');
  const [formData, setFormData] = useState({
    title: '',
    authors: [],
    isbn: '',
    description: '',
    categories: [],
    language: 'fr',
    format: 'physical',
    price: 0,
    cover_image: '',
    physical_copies: 0
  });
  const [authorInput, setAuthorInput] = useState('');
  const [categoryInput, setCategoryInput] = useState('');
  const [uploadingFile, setUploadingFile] = useState(false);

  useEffect(() => {
    fetchBooks();
  }, [token, user.school_id]);

  const fetchBooks = async () => {
    try {
      let url = `${API}/books`;
      if (user.role !== 'super_admin' && user.school_id) {
        url += `?school_id=${user.school_id}`;
      }
      
      const response = await axios.get(url, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setBooks(response.data);
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Erreur",
        description: "Impossible de charger les livres"
      });
    }
    setLoading(false);
  };

  const resetForm = () => {
    setFormData({
      title: '',
      authors: [],
      isbn: '',
      description: '',
      categories: [],
      language: 'fr',
      format: 'physical',
      price: 0,
      cover_image: '',
      physical_copies: 0
    });
    setAuthorInput('');
    setCategoryInput('');
    setEditingBook(null);
  };

  const handleAddAuthor = () => {
    if (authorInput.trim() && !formData.authors.includes(authorInput.trim())) {
      setFormData({
        ...formData,
        authors: [...formData.authors, authorInput.trim()]
      });
      setAuthorInput('');
    }
  };

  const handleRemoveAuthor = (author) => {
    setFormData({
      ...formData,
      authors: formData.authors.filter(a => a !== author)
    });
  };

  const handleAddCategory = () => {
    if (categoryInput.trim() && !formData.categories.includes(categoryInput.trim())) {
      setFormData({
        ...formData,
        categories: [...formData.categories, categoryInput.trim()]
      });
      setCategoryInput('');
    }
  };

  const handleRemoveCategory = (category) => {
    setFormData({
      ...formData,
      categories: formData.categories.filter(c => c !== category)
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      if (editingBook) {
        // Update existing book
        await axios.put(`${API}/books/${editingBook.id}`, formData, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast({
          title: "Livre modifié",
          description: "Le livre a été modifié avec succès"
        });
      } else {
        // Create new book
        await axios.post(`${API}/books`, formData, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast({
          title: "Livre ajouté",
          description: "Le livre a été ajouté avec succès"
        });
      }
      
      fetchBooks();
      setShowAddDialog(false);
      setShowEditDialog(false);
      resetForm();
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Erreur",
        description: error.response?.data?.detail || "Erreur lors de l'enregistrement"
      });
    }
    setLoading(false);
  };

  const handleEdit = (book) => {
    setEditingBook(book);
    setFormData({
      title: book.title,
      authors: book.authors || [],
      isbn: book.isbn || '',
      description: book.description || '',
      categories: book.categories || [],
      language: book.language || 'fr',
      format: book.format || 'physical',
      price: book.price || 0,
      cover_image: book.cover_image || '',
      physical_copies: 0 // This would need to be calculated from copies
    });
    setShowEditDialog(true);
  };

  const handleDelete = async (bookId) => {
    try {
      await axios.delete(`${API}/books/${bookId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast({
        title: "Livre supprimé",
        description: "Le livre a été supprimé avec succès"
      });
      fetchBooks();
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Erreur",
        description: "Impossible de supprimer le livre"
      });
    }
  };

  const handleFileUpload = async (bookId, file) => {
    if (!file) return;
    
    setUploadingFile(true);
    const uploadFormData = new FormData();
    uploadFormData.append('file', file);

    try {
      await axios.post(`${API}/books/${bookId}/upload-file`, uploadFormData, {
        headers: { 
          Authorization: `Bearer ${token}`,
          'Content-Type': 'multipart/form-data'
        }
      });
      toast({
        title: "Fichier uploadé",
        description: "Le fichier numérique a été uploadé avec succès"
      });
      fetchBooks();
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Erreur",
        description: "Erreur lors de l'upload du fichier"
      });
    }
    setUploadingFile(false);
  };

  const filteredBooks = books.filter(book => {
    const matchesSearch = book.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         book.authors?.some(author => author.toLowerCase().includes(searchTerm.toLowerCase())) ||
                         book.description?.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesFormat = filterFormat === 'all' || book.format === filterFormat;
    
    return matchesSearch && matchesFormat;
  });

  const BookForm = () => (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="title">Titre *</Label>
          <Input
            id="title"
            value={formData.title}
            onChange={(e) => setFormData({...formData, title: e.target.value})}
            required
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="isbn">ISBN</Label>
          <Input
            id="isbn"
            value={formData.isbn}
            onChange={(e) => setFormData({...formData, isbn: e.target.value})}
          />
        </div>
      </div>

      <div className="space-y-2">
        <Label>Auteurs</Label>
        <div className="flex gap-2 mb-2">
          <Input
            placeholder="Nom de l'auteur"
            value={authorInput}
            onChange={(e) => setAuthorInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddAuthor())}
          />
          <Button type="button" onClick={handleAddAuthor}>
            <Plus className="h-4 w-4" />
          </Button>
        </div>
        <div className="flex flex-wrap gap-2">
          {formData.authors.map((author, index) => (
            <Badge key={index} variant="secondary" className="cursor-pointer" onClick={() => handleRemoveAuthor(author)}>
              {author} ×
            </Badge>
          ))}
        </div>
      </div>

      <div className="space-y-2">
        <Label>Catégories</Label>
        <div className="flex gap-2 mb-2">
          <Input
            placeholder="Catégorie"
            value={categoryInput}
            onChange={(e) => setCategoryInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddCategory())}
          />
          <Button type="button" onClick={handleAddCategory}>
            <Plus className="h-4 w-4" />
          </Button>
        </div>
        <div className="flex flex-wrap gap-2">
          {formData.categories.map((category, index) => (
            <Badge key={index} variant="outline" className="cursor-pointer" onClick={() => handleRemoveCategory(category)}>
              {category} ×
            </Badge>
          ))}
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="description">Description</Label>
        <Textarea
          id="description"
          value={formData.description}
          onChange={(e) => setFormData({...formData, description: e.target.value})}
          rows={3}
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="space-y-2">
          <Label htmlFor="format">Format</Label>
          <Select value={formData.format} onValueChange={(value) => setFormData({...formData, format: value})}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="physical">Physique</SelectItem>
              <SelectItem value="digital">Numérique</SelectItem>
              <SelectItem value="both">Les deux</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-2">
          <Label htmlFor="language">Langue</Label>
          <Select value={formData.language} onValueChange={(value) => setFormData({...formData, language: value})}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="fr">Français</SelectItem>
              <SelectItem value="en">Anglais</SelectItem>
              <SelectItem value="es">Espagnol</SelectItem>
              <SelectItem value="de">Allemand</SelectItem>
            </SelectContent>
          </Select>
        </div>
        {(formData.format === 'physical' || formData.format === 'both') && (
          <div className="space-y-2">
            <Label htmlFor="physical_copies">Exemplaires physiques</Label>
            <Input
              id="physical_copies"
              type="number"
              min="0"
              value={formData.physical_copies}
              onChange={(e) => setFormData({...formData, physical_copies: parseInt(e.target.value) || 0})}
            />
          </div>
        )}
      </div>

      <div className="flex justify-end space-x-2">
        <Button 
          type="button" 
          variant="outline" 
          onClick={() => {
            setShowAddDialog(false);
            setShowEditDialog(false);
            resetForm();
          }}
        >
          Annuler
        </Button>
        <Button type="submit" disabled={loading}>
          {loading ? 'Enregistrement...' : (editingBook ? 'Modifier' : 'Ajouter')}
        </Button>
      </div>
    </form>
  );

  if (loading && books.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600"></div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Gestion des livres</h1>
          <p className="text-gray-600 mt-2">Gérez les livres de votre collection</p>
        </div>
        
        <Dialog open={showAddDialog} onOpenChange={setShowAddDialog}>
          <DialogTrigger asChild>
            <Button className="bg-emerald-600 hover:bg-emerald-700">
              <Plus className="h-4 w-4 mr-2" />
              Ajouter un livre
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Ajouter un nouveau livre</DialogTitle>
            </DialogHeader>
            <BookForm />
          </DialogContent>
        </Dialog>

        <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Modifier le livre</DialogTitle>
            </DialogHeader>
            <BookForm />
          </DialogContent>
        </Dialog>
      </div>

      {/* Search and Filter Bar */}
      <div className="bg-white p-6 rounded-lg shadow-sm border mb-6">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
            <Input
              placeholder="Rechercher par titre, auteur ou description..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
          <div className="flex gap-2">
            <Select value={filterFormat} onValueChange={setFilterFormat}>
              <SelectTrigger className="w-48">
                <Filter className="h-4 w-4 mr-2" />
                <SelectValue placeholder="Format" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Tous les formats</SelectItem>
                <SelectItem value="physical">Physique</SelectItem>
                <SelectItem value="digital">Numérique</SelectItem>
                <SelectItem value="both">Les deux</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </div>

      {/* Books Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredBooks.map((book) => (
          <Card key={book.id} className="group hover:shadow-lg transition-shadow">
            <CardHeader className="pb-4">
              <div className="flex justify-between items-start">
                <div className="flex-1 min-w-0">
                  <CardTitle className="text-lg truncate">{book.title}</CardTitle>
                  <p className="text-sm text-gray-600 mt-1">
                    {book.authors?.join(', ') || 'Auteur inconnu'}
                  </p>
                </div>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="sm" className="opacity-0 group-hover:opacity-100 transition-opacity">
                      <MoreHorizontal className="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem onClick={() => handleEdit(book)}>
                      <Edit className="h-4 w-4 mr-2" />
                      Modifier
                    </DropdownMenuItem>
                    {(book.format === 'digital' || book.format === 'both') && (
                      <DropdownMenuItem asChild>
                        <label className="flex items-center cursor-pointer">
                          <Upload className="h-4 w-4 mr-2" />
                          Upload fichier
                          <input
                            type="file"
                            accept=".pdf,.epub"
                            className="hidden"
                            onChange={(e) => e.target.files[0] && handleFileUpload(book.id, e.target.files[0])}
                            disabled={uploadingFile}
                          />
                        </label>
                      </DropdownMenuItem>
                    )}
                    <AlertDialog>
                      <AlertDialogTrigger asChild>
                        <DropdownMenuItem onSelect={(e) => e.preventDefault()}>
                          <Trash2 className="h-4 w-4 mr-2" />
                          Supprimer
                        </DropdownMenuItem>
                      </AlertDialogTrigger>
                      <AlertDialogContent>
                        <AlertDialogHeader>
                          <AlertDialogTitle>Confirmer la suppression</AlertDialogTitle>
                          <AlertDialogDescription>
                            Êtes-vous sûr de vouloir supprimer le livre "{book.title}" ? Cette action est irréversible.
                          </AlertDialogDescription>
                        </AlertDialogHeader>
                        <AlertDialogFooter>
                          <AlertDialogCancel>Annuler</AlertDialogCancel>
                          <AlertDialogAction onClick={() => handleDelete(book.id)}>
                            Supprimer
                          </AlertDialogAction>
                        </AlertDialogFooter>
                      </AlertDialogContent>
                    </AlertDialog>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {book.categories && book.categories.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {book.categories.slice(0, 3).map((category, index) => (
                      <Badge key={index} variant="outline" className="text-xs">
                        {category}
                      </Badge>
                    ))}
                    {book.categories.length > 3 && (
                      <Badge variant="outline" className="text-xs">
                        +{book.categories.length - 3}
                      </Badge>
                    )}
                  </div>
                )}
                
                <div className="flex items-center justify-between">
                  <Badge 
                    variant={book.format === 'physical' ? 'default' : book.format === 'digital' ? 'secondary' : 'outline'}
                    className="text-xs"
                  >
                    {book.format === 'physical' ? 'Physique' : book.format === 'digital' ? 'Numérique' : 'Hybride'}
                  </Badge>
                  <div className="text-sm text-gray-500">
                    {book.language === 'fr' ? 'Français' : book.language.toUpperCase()}
                  </div>
                </div>

                {book.description && (
                  <p className="text-sm text-gray-600 line-clamp-3">
                    {book.description}
                  </p>
                )}

                <div className="text-xs text-gray-400 border-t pt-3">
                  Ajouté le {new Date(book.created_at).toLocaleDateString()}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {filteredBooks.length === 0 && (
        <div className="text-center py-12">
          <BookOpen className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Aucun livre trouvé</h3>
          <p className="text-gray-600 mb-4">
            {searchTerm || filterFormat !== 'all' 
              ? "Aucun livre ne correspond à vos critères de recherche."
              : "Commencez par ajouter votre premier livre."}
          </p>
          {(!searchTerm && filterFormat === 'all') && (
            <Button onClick={() => setShowAddDialog(true)} className="bg-emerald-600 hover:bg-emerald-700">
              <Plus className="h-4 w-4 mr-2" />
              Ajouter un livre
            </Button>
          )}
        </div>
      )}
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
                    <Catalogue />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/manage-books" 
                element={
                  <ProtectedRoute roles={['school_admin', 'librarian', 'teacher']}>
                    <ManageBooks />
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