"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import api from "@/lib/axios";
import { useStore } from "@/lib/store";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Loader2, Search, Filter, ShoppingCart, Info, Plus, Minus, X } from "lucide-react";
import Link from "next/link";

interface Category {
  id: number;
  name: string;
}

interface MenuItem {
  id: number;
  category_id: number;
  name: string;
  description: string;
  price: number;
  image_url: string;
  is_complimentary: boolean;
  prep_time_min: number;
  tags: string[];
}

export default function DigitalMenuPage() {
  const [activeCategory, setActiveCategory] = useState<number | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [isCartOpen, setIsCartOpen] = useState(false);

  const { cart, addToCart, removeFromCart, updateQuantity, cartTotal } = useStore();

  const { data: categories } = useQuery({
    queryKey: ['categories'],
    queryFn: async () => {
      const res = await api.get<Category[]>('/menu/categories');
      return res.data;
    }
  });

  const { data: menuItems, isLoading } = useQuery({
    queryKey: ['menu', activeCategory, searchQuery],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (activeCategory) params.append('category_id', activeCategory.toString());
      if (searchQuery) params.append('search', searchQuery);
      const res = await api.get<MenuItem[]>(`/menu?${params.toString()}`);
      return res.data;
    }
  });

  // Calculate cart items count
  const cartItemCount = cart.reduce((total, item) => total + item.quantity, 0);

  return (
    <div className="min-h-screen bg-slate-50 pb-24">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-md sticky top-0 z-40 border-b border-blue-100 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <Link href="/" className="font-bold text-xl text-slate-800">
            Arjuna <span className="text-primary">Menu</span>
          </Link>
          <button 
            onClick={() => setIsCartOpen(true)}
            className="relative p-2 text-slate-600 hover:text-primary transition-colors"
          >
            <ShoppingCart className="w-6 h-6" />
            {cartItemCount > 0 && (
              <span className="absolute top-0 right-0 w-5 h-5 bg-red-500 text-white text-xs font-bold flex items-center justify-center rounded-full">
                {cartItemCount}
              </span>
            )}
          </button>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Search & Filter */}
        <div className="flex flex-col sm:flex-row gap-4 mb-8">
          <div className="relative flex-grow">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
            <Input 
              placeholder="Cari makanan atau minuman..." 
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 h-12 rounded-2xl border-slate-200 bg-white shadow-sm focus-visible:ring-primary"
            />
          </div>
          <Button variant="outline" className="h-12 px-6 rounded-2xl border-slate-200 bg-white">
            <Filter className="w-5 h-5 mr-2 text-slate-500" />
            Filter
          </Button>
        </div>

        {/* Categories */}
        <div className="flex gap-3 overflow-x-auto no-scrollbar mb-8 pb-2">
          <button
            onClick={() => setActiveCategory(null)}
            className={`whitespace-nowrap px-6 py-2.5 rounded-full text-sm font-semibold transition-all shadow-sm ${
              activeCategory === null 
                ? 'bg-primary text-white shadow-blue-200' 
                : 'bg-white text-slate-600 border border-slate-200 hover:border-blue-300'
            }`}
          >
            Semua Menu
          </button>
          {categories?.map((cat) => (
            <button
              key={cat.id}
              onClick={() => setActiveCategory(cat.id)}
              className={`whitespace-nowrap px-6 py-2.5 rounded-full text-sm font-semibold transition-all shadow-sm ${
                activeCategory === cat.id 
                  ? 'bg-primary text-white shadow-blue-200' 
                  : 'bg-white text-slate-600 border border-slate-200 hover:border-blue-300'
              }`}
            >
              {cat.name}
            </button>
          ))}
        </div>

        {/* Menu Grid */}
        {isLoading ? (
          <div className="flex justify-center py-20">
            <Loader2 className="w-10 h-10 animate-spin text-primary" />
          </div>
        ) : menuItems?.length === 0 ? (
          <div className="text-center py-20 text-slate-500">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-slate-100 mb-4">
              <Search className="w-8 h-8 text-slate-400" />
            </div>
            <p className="text-lg">Tidak ada menu yang sesuai kriteria.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {menuItems?.map((item) => (
              <Card key={item.id} className="border-0 shadow-md hover:shadow-xl transition-all duration-300 overflow-hidden rounded-2xl group flex flex-col">
                <div className="relative h-48 bg-slate-200 overflow-hidden">
                  {item.image_url ? (
                    <img src={item.image_url} alt={item.name} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center bg-blue-50 text-blue-200">
                      <span className="text-4xl">🍽️</span>
                    </div>
                  )}
                  {item.is_complimentary && (
                    <div className="absolute top-3 right-3 bg-green-500 text-white text-xs font-bold px-3 py-1 rounded-full shadow-md">
                      GRATIS
                    </div>
                  )}
                </div>
                <CardContent className="p-5 flex-grow flex flex-col">
                  <div className="flex justify-between items-start mb-2">
                    <h3 className="font-bold text-lg text-slate-800 line-clamp-1">{item.name}</h3>
                  </div>
                  <p className="text-slate-500 text-sm line-clamp-2 mb-4 flex-grow">{item.description}</p>
                  
                  <div className="flex items-center justify-between mt-auto">
                    <div>
                      {item.is_complimentary ? (
                        <span className="font-bold text-green-600 text-lg">Rp 0</span>
                      ) : (
                        <span className="font-bold text-slate-800 text-lg">
                          Rp {new Intl.NumberFormat('id-ID').format(item.price)}
                        </span>
                      )}
                      <div className="text-xs text-slate-400 flex items-center mt-1">
                        <Clock className="w-3 h-3 mr-1" /> {item.prep_time_min} mnt
                      </div>
                    </div>
                    <Button 
                      onClick={() => addToCart({ id: item.id, name: item.name, price: Number(item.price) })}
                      size="sm" 
                      className="rounded-xl px-4 shadow-md bg-primary hover:bg-blue-600"
                    >
                      Tambah
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </main>

      {/* Cart Sidebar Overlay */}
      {isCartOpen && (
        <div className="fixed inset-0 z-50 flex justify-end">
          <div className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm transition-opacity" onClick={() => setIsCartOpen(false)}></div>
          <div className="relative w-full max-w-md bg-white h-full shadow-2xl flex flex-col animate-in slide-in-from-right-full duration-300">
            <div className="flex items-center justify-between p-4 border-b border-slate-100">
              <h2 className="text-lg font-bold text-slate-800 flex items-center">
                <ShoppingCart className="w-5 h-5 mr-2 text-primary" /> Pesanan Anda
              </h2>
              <button onClick={() => setIsCartOpen(false)} className="p-2 text-slate-400 hover:text-slate-600 rounded-full hover:bg-slate-100 transition-colors">
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <div className="flex-grow overflow-y-auto p-4">
              {cart.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center text-slate-500 space-y-4">
                  <div className="w-20 h-20 bg-slate-50 rounded-full flex items-center justify-center">
                    <ShoppingCart className="w-10 h-10 text-slate-300" />
                  </div>
                  <p>Keranjang pesanan masih kosong</p>
                  <Button variant="outline" onClick={() => setIsCartOpen(false)} className="rounded-xl">Lihat Menu</Button>
                </div>
              ) : (
                <div className="space-y-4">
                  {cart.map((item) => (
                    <div key={item.id} className="flex items-start justify-between p-4 bg-slate-50 rounded-2xl border border-slate-100">
                      <div className="flex-grow pr-4">
                        <h4 className="font-semibold text-slate-800 leading-tight">{item.name}</h4>
                        <p className="text-primary font-medium text-sm mt-1">Rp {new Intl.NumberFormat('id-ID').format(item.price)}</p>
                        
                        <div className="flex items-center gap-3 mt-3">
                          <button 
                            onClick={() => item.quantity > 1 ? updateQuantity(item.id, item.quantity - 1) : removeFromCart(item.id)}
                            className="w-8 h-8 flex items-center justify-center rounded-lg bg-white border border-slate-200 text-slate-600 shadow-sm hover:border-primary hover:text-primary transition-colors"
                          >
                            <Minus className="w-4 h-4" />
                          </button>
                          <span className="font-bold w-4 text-center text-slate-700">{item.quantity}</span>
                          <button 
                            onClick={() => updateQuantity(item.id, item.quantity + 1)}
                            className="w-8 h-8 flex items-center justify-center rounded-lg bg-white border border-slate-200 text-slate-600 shadow-sm hover:border-primary hover:text-primary transition-colors"
                          >
                            <Plus className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="font-bold text-slate-800">
                          Rp {new Intl.NumberFormat('id-ID').format(item.price * item.quantity)}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
            
            {cart.length > 0 && (
              <div className="p-6 bg-white border-t border-slate-100 shadow-[0_-10px_40px_rgba(0,0,0,0.05)]">
                <div className="flex justify-between items-center mb-6">
                  <span className="text-slate-500 font-medium">Total Pesanan</span>
                  <span className="text-2xl font-bold text-slate-800">
                    Rp {new Intl.NumberFormat('id-ID').format(cartTotal())}
                  </span>
                </div>
                <Link href="/order/checkout">
                  <Button className="w-full h-14 rounded-2xl text-lg font-bold shadow-xl shadow-primary/30">
                    Lanjut Pembayaran
                  </Button>
                </Link>
              </div>
            )}
          </div>
        </div>
      )}

    </div>
  );
}
