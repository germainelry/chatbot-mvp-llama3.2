/**
 * Tenant Management Page
 * Admin interface for creating and managing tenants.
 */
import { useState, useEffect } from 'react';
import { Users, Plus, Edit2, Trash2, Save, X } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Alert, AlertDescription, AlertTitle } from '../components/ui/alert';
import { PageHeader } from '../components/layout/PageHeader';
import { Badge } from '../components/ui/badge';
import { createTenant, listTenants, updateTenant, deleteTenant, Tenant } from '../services/api';

export default function TenantManagement() {
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [editingTenant, setEditingTenant] = useState<Partial<Tenant> | null>(null);
  const [loading, setLoading] = useState(true);
  const [alert, setAlert] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  useEffect(() => {
    loadTenants();
  }, []);

  const loadTenants = async () => {
    try {
      const data = await listTenants();
      setTenants(data);
    } catch (error) {
      console.error('Failed to load tenants:', error);
      setAlert({ type: 'error', message: 'Failed to load tenants' });
      setTimeout(() => setAlert(null), 3000);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setEditingTenant({ name: '', slug: '', is_active: 1 });
  };

  const handleEdit = (tenant: Tenant) => {
    setEditingTenant(tenant);
  };

  const handleSave = async () => {
    if (!editingTenant || !editingTenant.name || !editingTenant.slug) return;
    
    try {
      if (editingTenant.id) {
        await updateTenant(editingTenant.id, editingTenant);
      } else {
        await createTenant({
          name: editingTenant.name,
          slug: editingTenant.slug,
          is_active: editingTenant.is_active || 1,
        });
      }
      setAlert({ type: 'success', message: 'Tenant saved successfully' });
      setTimeout(() => {
        setAlert(null);
        setEditingTenant(null);
        loadTenants();
      }, 2000);
    } catch (error: any) {
      setAlert({ type: 'error', message: error.response?.data?.detail || 'Failed to save tenant' });
      setTimeout(() => setAlert(null), 3000);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this tenant? This will delete all associated data.')) return;
    
    try {
      await deleteTenant(id);
      setAlert({ type: 'success', message: 'Tenant deleted successfully' });
      setTimeout(() => {
        setAlert(null);
        loadTenants();
      }, 2000);
    } catch (error) {
      setAlert({ type: 'error', message: 'Failed to delete tenant' });
      setTimeout(() => setAlert(null), 3000);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Tenant Management"
        description="Create and manage tenants for multi-tenant deployment"
      />

      {alert && (
        <Alert variant={alert.type === 'error' ? 'destructive' : 'default'}>
          <AlertTitle>{alert.type === 'error' ? 'Error' : 'Success'}</AlertTitle>
          <AlertDescription>{alert.message}</AlertDescription>
        </Alert>
      )}

      {editingTenant ? (
        <Card>
          <CardHeader>
            <CardTitle>{editingTenant.id ? 'Edit Tenant' : 'Create New Tenant'}</CardTitle>
            <CardDescription>
              {editingTenant.id ? 'Update tenant information' : 'Create a new tenant for client deployment'}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">Tenant Name</Label>
              <Input
                id="name"
                value={editingTenant.name || ''}
                onChange={(e) => setEditingTenant({ ...editingTenant, name: e.target.value })}
                placeholder="e.g., Acme Corporation"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="slug">Slug (Unique Identifier)</Label>
              <Input
                id="slug"
                value={editingTenant.slug || ''}
                onChange={(e) => setEditingTenant({ ...editingTenant, slug: e.target.value.toLowerCase().replace(/\s+/g, '-') })}
                placeholder="e.g., acme-corp"
              />
              <p className="text-sm text-muted-foreground">
                Used as unique identifier. Lowercase, no spaces.
              </p>
            </div>

            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="is_active"
                checked={editingTenant.is_active === 1}
                onChange={(e) => setEditingTenant({ ...editingTenant, is_active: e.target.checked ? 1 : 0 })}
                className="h-4 w-4"
              />
              <Label htmlFor="is_active">Active</Label>
            </div>

            <div className="flex gap-2">
              <Button onClick={handleSave}>
                <Save className="h-4 w-4 mr-2" />
                Save
              </Button>
              <Button variant="outline" onClick={() => setEditingTenant(null)}>
                <X className="h-4 w-4 mr-2" />
                Cancel
              </Button>
            </div>
          </CardContent>
        </Card>
      ) : (
        <>
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-2xl font-bold">Tenants</h2>
              <p className="text-muted-foreground">Manage all tenants in the system</p>
            </div>
            <Button onClick={handleCreate}>
              <Plus className="h-4 w-4 mr-2" />
              Create Tenant
            </Button>
          </div>

          {loading ? (
            <div>Loading tenants...</div>
          ) : tenants.length === 0 ? (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12">
                <Users className="h-12 w-12 text-muted-foreground mb-4" />
                <p className="text-muted-foreground mb-4">No tenants found</p>
                <Button onClick={handleCreate}>
                  <Plus className="h-4 w-4 mr-2" />
                  Create Your First Tenant
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {tenants.map((tenant) => (
                <Card key={tenant.id}>
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div>
                        <CardTitle>{tenant.name}</CardTitle>
                        <CardDescription>Slug: {tenant.slug}</CardDescription>
                      </div>
                      <Badge variant={tenant.is_active === 1 ? 'default' : 'secondary'}>
                        {tenant.is_active === 1 ? 'Active' : 'Inactive'}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2 text-sm text-muted-foreground">
                      <p>Created: {new Date(tenant.created_at).toLocaleDateString()}</p>
                      <p>Updated: {new Date(tenant.updated_at).toLocaleDateString()}</p>
                    </div>
                    <div className="flex gap-2 mt-4">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleEdit(tenant)}
                      >
                        <Edit2 className="h-3 w-3 mr-1" />
                        Edit
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleDelete(tenant.id)}
                        className="text-destructive hover:text-destructive"
                      >
                        <Trash2 className="h-3 w-3 mr-1" />
                        Delete
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}

