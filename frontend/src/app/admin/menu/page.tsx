"use client";

import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import api from "@/lib/axios";
import { useToast } from "@/hooks/use-toast";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Loader2, Plus, Edit2, Trash2, Image as ImageIcon } from "lucide-react";

export default function AdminMenuPage() {
  const { toast } = useToast();
  const [activeTab, setActiveTab] = useState<'items' | 'categories'>('items');

  const { data: categories, isLoading: loadingCats, refetch: refetchCats } = useQuery({
    queryKey: ['admin_categories'],
    queryFn: async () => {
      const res = await api.get('/menu/categories');
      return res.data;
    }
  });

  const { data: items, isLoading: loadingItems, refetch: refetchItems } = useQuery({
    queryKey: ['admin_menu_items'],
    queryFn: async () => {
      const res = await api.get('/menu');
      return res.data;
    }
  });

  const deleteCategory = useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/admin/menu/categories/${id}`);
    },
    onSuccess: () => {
      toast({ title: "Berhasil", description: "Kategori dihapus" });
      refetchCats();
    },
    onError: (err: any) => {
      toast({ title: "Gagal", description: err.response?.data?.detail, variant: "destructive" });
    }
  });

  const deleteItem = useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/admin/menu/items/${id}`);
    },
    onSuccess: () => {
      toast({ title: "Berhasil", description: "Menu dihapus" });
      refetchItems();
    },
    onError: (err: any) => {
      toast({ title: "Gagal", description: err.response?.data?.detail, variant: "destructive" });
    }
  });

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center bg-white p-4 rounded-2xl shadow-sm border border-slate-100">
        <div className="flex gap-2">
          <Button 
            variant={activeTab === 'items' ? 'default' : 'ghost'} 
            onClick={() => setActiveTab('items')}
            className={`rounded-xl ${activeTab === 'items' ? 'bg-blue-600 hover:bg-blue-700' : ''}`}
          >
            Daftar Menu
          </Button>
          <Button 
            variant={activeTab === 'categories' ? 'default' : 'ghost'} 
            onClick={() => setActiveTab('categories')}
            className={`rounded-xl ${activeTab === 'categories' ? 'bg-blue-600 hover:bg-blue-700' : ''}`}
          >
            Kategori
          </Button>
        </div>
        <Button className="bg-blue-600 hover:bg-blue-700 rounded-xl">
          <Plus className="w-4 h-4 mr-2" />
          Tambah {activeTab === 'items' ? 'Menu' : 'Kategori'}
        </Button>
      </div>

      {activeTab === 'items' && (
        <Card className="border-0 shadow-md rounded-2xl overflow-hidden">
          <CardHeader className="bg-white border-b border-slate-100 pb-4">
            <div className="flex justify-between items-center">
              <CardTitle className="text-xl text-slate-800">Manajemen Menu Makanan & Minuman</CardTitle>
              <Input placeholder="Cari menu..." className="w-64 rounded-xl bg-slate-50" />
            </div>
          </CardHeader>
          <CardContent className="p-0">
            {loadingItems ? (
              <div className="flex justify-center py-12"><Loader2 className="w-8 h-8 animate-spin text-blue-600" /></div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-slate-50 text-slate-500 text-sm border-b border-slate-100">
                      <th className="p-4 font-semibold w-16">Foto</th>
                      <th className="p-4 font-semibold">Nama Menu</th>
                      <th className="p-4 font-semibold">Harga</th>
                      <th className="p-4 font-semibold">Status</th>
                      <th className="p-4 font-semibold text-right">Aksi</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 text-sm">
                    {items?.map((item: any) => (
                      <tr key={item.id} className="hover:bg-slate-50 transition-colors">
                        <td className="p-4">
                          <div className="w-12 h-12 rounded-lg bg-slate-200 overflow-hidden flex items-center justify-center">
                            {item.image_url ? (
                              <img src={item.image_url} alt={item.name} className="w-full h-full object-cover" />
                            ) : (
                              <ImageIcon className="w-5 h-5 text-slate-400" />
                            )}
                          </div>
                        </td>
                        <td className="p-4 font-medium text-slate-800">{item.name}</td>
                        <td className="p-4">Rp {new Intl.NumberFormat('id-ID').format(item.price)}</td>
                        <td className="p-4">
                          <span className={`px-2.5 py-1 rounded-full text-xs font-semibold ${item.is_available ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                            {item.is_available ? 'Tersedia' : 'Habis'}
                          </span>
                        </td>
                        <td className="p-4 text-right">
                          <Button variant="ghost" size="icon" className="text-slate-500 hover:text-blue-600"><Edit2 className="w-4 h-4" /></Button>
                          <Button variant="ghost" size="icon" className="text-slate-500 hover:text-red-600" onClick={() => deleteItem.mutate(item.id)}><Trash2 className="w-4 h-4" /></Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {activeTab === 'categories' && (
        <Card className="border-0 shadow-md rounded-2xl overflow-hidden">
          <CardHeader className="bg-white border-b border-slate-100 pb-4">
            <CardTitle className="text-xl text-slate-800">Manajemen Kategori</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            {loadingCats ? (
              <div className="flex justify-center py-12"><Loader2 className="w-8 h-8 animate-spin text-blue-600" /></div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-slate-50 text-slate-500 text-sm border-b border-slate-100">
                      <th className="p-4 font-semibold">Nama Kategori</th>
                      <th className="p-4 font-semibold">Status</th>
                      <th className="p-4 font-semibold text-right">Aksi</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 text-sm">
                    {categories?.map((cat: any) => (
                      <tr key={cat.id} className="hover:bg-slate-50 transition-colors">
                        <td className="p-4 font-medium text-slate-800">{cat.name}</td>
                        <td className="p-4">
                          <span className={`px-2.5 py-1 rounded-full text-xs font-semibold ${cat.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                            {cat.is_active ? 'Aktif' : 'Nonaktif'}
                          </span>
                        </td>
                        <td className="p-4 text-right">
                          <Button variant="ghost" size="icon" className="text-slate-500 hover:text-blue-600"><Edit2 className="w-4 h-4" /></Button>
                          <Button variant="ghost" size="icon" className="text-slate-500 hover:text-red-600" onClick={() => deleteCategory.mutate(cat.id)}><Trash2 className="w-4 h-4" /></Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
