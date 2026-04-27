"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, Utensils, Users, Settings, FileText, LogOut, Coffee } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  
  if (pathname === '/admin/login') {
    return <>{children}</>;
  }

  const navigation = [
    { name: 'Dashboard', href: '/admin/dashboard', icon: LayoutDashboard },
    { name: 'Menu & Kategori', href: '/admin/menu', icon: Utensils },
    { name: 'Laporan', href: '/admin/reports', icon: FileText },
    { name: 'Manajemen User', href: '/admin/users', icon: Users },
    { name: 'Pengaturan', href: '/admin/settings', icon: Settings },
  ];

  return (
    <div className="min-h-screen bg-slate-50 flex">
      {/* Sidebar */}
      <aside className="w-64 bg-slate-900 text-slate-300 flex-shrink-0 flex flex-col fixed inset-y-0 z-10 shadow-xl">
        <div className="h-20 flex items-center px-6 bg-slate-950 border-b border-slate-800">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-blue-500 text-white rounded-lg flex items-center justify-center font-bold">
              <Coffee className="w-5 h-5" />
            </div>
            <span className="font-bold text-lg text-white tracking-tight">Admin Area</span>
          </div>
        </div>
        
        <div className="p-4 flex-grow space-y-1">
          {navigation.map((item) => {
            const isActive = pathname.startsWith(item.href);
            return (
              <Link key={item.name} href={item.href}>
                <div className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
                  isActive 
                    ? 'bg-blue-600 text-white font-medium shadow-md shadow-blue-900' 
                    : 'hover:bg-slate-800 hover:text-white'
                }`}>
                  <item.icon className="w-5 h-5" />
                  {item.name}
                </div>
              </Link>
            )
          })}
        </div>
        
        <div className="p-4 border-t border-slate-800">
          <Button variant="ghost" className="w-full justify-start text-slate-400 hover:text-white hover:bg-slate-800 rounded-xl">
            <LogOut className="w-5 h-5 mr-3" /> Logout
          </Button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 ml-64 flex flex-col min-h-screen">
        <header className="h-20 bg-white/80 backdrop-blur-md sticky top-0 z-20 border-b border-slate-200 px-8 flex items-center justify-between">
          <h1 className="text-xl font-bold text-slate-800">
            {navigation.find(n => pathname.startsWith(n.href))?.name || 'Administrator'}
          </h1>
          <div className="flex items-center gap-4">
            <div className="text-sm text-right">
              <p className="font-semibold text-slate-800">Super Admin</p>
            </div>
            <div className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center text-white font-bold">
              SA
            </div>
          </div>
        </header>
        
        <div className="p-8 flex-grow">
          {children}
        </div>
      </main>
    </div>
  );
}
