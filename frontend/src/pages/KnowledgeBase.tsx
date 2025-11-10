/**
 * Knowledge Base Management
 * Interface for agents to add/edit/delete knowledge base articles.
 * Simple RAG implementation for AI context.
 */
import { useState, useEffect } from 'react';
import { Plus, Edit2, Trash2, Search, BookOpen, Save, X } from 'lucide-react';
import {
  getKnowledgeArticles,
  createKnowledgeArticle,
  updateKnowledgeArticle,
  deleteKnowledgeArticle,
  KnowledgeArticle,
} from '../services/api';

export default function KnowledgeBase() {
  const [articles, setArticles] = useState<KnowledgeArticle[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [isEditing, setIsEditing] = useState(false);
  const [editingArticle, setEditingArticle] = useState<Partial<KnowledgeArticle>>({
    title: '',
    content: '',
    category: '',
    tags: '',
  });

  useEffect(() => {
    loadArticles();
  }, [selectedCategory, searchTerm]);

  const loadArticles = async () => {
    try {
      const data = await getKnowledgeArticles(
        selectedCategory || undefined,
        searchTerm || undefined
      );
      setArticles(data);
    } catch (error) {
      console.error('Failed to load articles:', error);
    }
  };

  const handleSave = async () => {
    try {
      if (editingArticle.id) {
        // Update existing
        await updateKnowledgeArticle(editingArticle.id, editingArticle);
      } else {
        // Create new
        await createKnowledgeArticle({
          title: editingArticle.title!,
          content: editingArticle.content!,
          category: editingArticle.category!,
          tags: editingArticle.tags || '',
        });
      }
      setIsEditing(false);
      setEditingArticle({ title: '', content: '', category: '', tags: '' });
      loadArticles();
    } catch (error) {
      console.error('Failed to save article:', error);
    }
  };

  const handleEdit = (article: KnowledgeArticle) => {
    setEditingArticle(article);
    setIsEditing(true);
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this article?')) return;
    
    try {
      await deleteKnowledgeArticle(id);
      loadArticles();
    } catch (error) {
      console.error('Failed to delete article:', error);
    }
  };

  const handleCancel = () => {
    setIsEditing(false);
    setEditingArticle({ title: '', content: '', category: '', tags: '' });
  };

  const categories = ['Returns', 'Shipping', 'Account', 'Products', 'Billing', 'Technical'];

  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Knowledge Base</h1>
        <p className="text-gray-600 mt-2">
          Manage articles for AI context and customer support
        </p>
      </div>

      {!isEditing ? (
        <>
          {/* Search and Filters */}
          <div className="bg-white rounded-lg shadow p-4 mb-6">
            <div className="flex flex-col md:flex-row gap-4">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5" />
                <input
                  type="text"
                  placeholder="Search articles..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:outline-none"
                />
              </div>
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:outline-none"
              >
                <option value="">All Categories</option>
                {categories.map((cat) => (
                  <option key={cat} value={cat}>
                    {cat}
                  </option>
                ))}
              </select>
              <button
                onClick={() => setIsEditing(true)}
                className="bg-primary-600 text-white px-6 py-2 rounded-lg hover:bg-primary-700 flex items-center whitespace-nowrap"
              >
                <Plus className="h-5 w-5 mr-2" />
                Add Article
              </button>
            </div>
          </div>

          {/* Articles Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {articles.length === 0 ? (
              <div className="col-span-2 text-center py-12">
                <BookOpen className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600">No articles found. Add your first article!</p>
              </div>
            ) : (
              articles.map((article) => (
                <div
                  key={article.id}
                  className="bg-white rounded-lg shadow hover:shadow-lg transition-shadow"
                >
                  <div className="p-6">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex-1">
                        <h3 className="text-lg font-semibold text-gray-900 mb-1">
                          {article.title}
                        </h3>
                        <span className="inline-block px-2 py-1 bg-primary-100 text-primary-800 text-xs rounded-full">
                          {article.category}
                        </span>
                      </div>
                      <div className="flex space-x-2 ml-4">
                        <button
                          onClick={() => handleEdit(article)}
                          className="p-2 text-gray-600 hover:text-primary-600 hover:bg-primary-50 rounded"
                        >
                          <Edit2 className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleDelete(article.id)}
                          className="p-2 text-gray-600 hover:text-red-600 hover:bg-red-50 rounded"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                    <p className="text-sm text-gray-600 mb-3 line-clamp-3">
                      {article.content}
                    </p>
                    {article.tags && (
                      <div className="flex flex-wrap gap-1">
                        {article.tags.split(',').map((tag, i) => (
                          <span
                            key={i}
                            className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded"
                          >
                            {tag.trim()}
                          </span>
                        ))}
                      </div>
                    )}
                    <p className="text-xs text-gray-400 mt-3">
                      Updated {new Date(article.updated_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
              ))
            )}
          </div>
        </>
      ) : (
        /* Edit/Create Form */
        <div className="bg-white rounded-lg shadow p-6">
          <div className="mb-6">
            <h2 className="text-2xl font-semibold text-gray-900">
              {editingArticle.id ? 'Edit Article' : 'New Article'}
            </h2>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Title *
              </label>
              <input
                type="text"
                value={editingArticle.title}
                onChange={(e) =>
                  setEditingArticle({ ...editingArticle, title: e.target.value })
                }
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:outline-none"
                placeholder="e.g., Return & Refund Policy"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Category *
              </label>
              <select
                value={editingArticle.category}
                onChange={(e) =>
                  setEditingArticle({ ...editingArticle, category: e.target.value })
                }
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:outline-none"
              >
                <option value="">Select category</option>
                {categories.map((cat) => (
                  <option key={cat} value={cat}>
                    {cat}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Content *
              </label>
              <textarea
                value={editingArticle.content}
                onChange={(e) =>
                  setEditingArticle({ ...editingArticle, content: e.target.value })
                }
                rows={12}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:outline-none"
                placeholder="Article content..."
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Tags (comma-separated)
              </label>
              <input
                type="text"
                value={editingArticle.tags}
                onChange={(e) =>
                  setEditingArticle({ ...editingArticle, tags: e.target.value })
                }
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:outline-none"
                placeholder="return, refund, policy, 30 days"
              />
            </div>

            <div className="flex space-x-3 pt-4">
              <button
                onClick={handleSave}
                disabled={
                  !editingArticle.title ||
                  !editingArticle.content ||
                  !editingArticle.category
                }
                className="flex-1 bg-primary-600 text-white px-6 py-2 rounded-lg hover:bg-primary-700 disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center justify-center"
              >
                <Save className="h-5 w-5 mr-2" />
                Save Article
              </button>
              <button
                onClick={handleCancel}
                className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center"
              >
                <X className="h-5 w-5 mr-2" />
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Info Box */}
      {!isEditing && (
        <div className="mt-8 bg-blue-50 rounded-lg p-6 border border-blue-200">
          <h3 className="text-lg font-semibold text-blue-900 mb-2">💡 Knowledge Base Tips</h3>
          <ul className="space-y-1 text-sm text-blue-800">
            <li>• Articles are used by AI to generate contextual responses</li>
            <li>• Use descriptive tags for better keyword matching</li>
            <li>• Keep content clear and concise for optimal AI comprehension</li>
            <li>• Review and update articles based on agent feedback</li>
            <li>• In production, would use vector embeddings for semantic search</li>
          </ul>
        </div>
      )}
    </div>
  );
}

