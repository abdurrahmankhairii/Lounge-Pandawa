import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { ArrowRight, Clock, Coffee, ShieldCheck, MapPin } from 'lucide-react';

export default function LandingPage() {
  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      <header className="bg-white/80 backdrop-blur-md sticky top-0 z-50 border-b border-blue-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-primary text-white rounded-xl flex items-center justify-center font-bold text-xl shadow-lg shadow-blue-200">
              A
            </div>
            <span className="font-bold text-2xl text-slate-800 tracking-tight">Arjuna <span className="text-primary">Lounge</span></span>
          </div>
          <div className="flex items-center gap-4">
            <Link href="/login">
              <Button variant="ghost" className="text-slate-600 font-medium">Masuk</Button>
            </Link>
            <Link href="/booking">
              <Button className="bg-primary hover:bg-primary/90 text-white shadow-md shadow-blue-200 rounded-xl px-6">
                Booking Sekarang
              </Button>
            </Link>
          </div>
        </div>
      </header>

      <main className="flex-grow">
        <section className="relative overflow-hidden pt-24 pb-32">
          <div className="absolute inset-0 bg-gradient-to-br from-blue-50 to-slate-50 z-0"></div>
          {/* Decorative Elements */}
          <div className="absolute top-20 left-10 w-72 h-72 bg-blue-300 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob"></div>
          <div className="absolute top-40 right-10 w-72 h-72 bg-blue-400 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-2000"></div>
          <div className="absolute -bottom-8 left-40 w-72 h-72 bg-blue-200 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-4000"></div>

          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10 text-center">
            <h1 className="text-5xl md:text-7xl font-extrabold text-slate-900 tracking-tight mb-8 animate-fade-in">
              Kenyamanan Eksekutif <br className="hidden md:block"/>
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-blue-600">
                Sebelum Penerbangan Anda
              </span>
            </h1>
            <p className="text-lg md:text-xl text-slate-600 max-w-2xl mx-auto mb-10 animate-slide-up">
              Fasilitas premium, hidangan lezat, dan pelayanan eksklusif menanti Anda di Arjuna VIP Lounge, Balai Kesehatan Penerbangan.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center animate-slide-up" style={{ animationDelay: '0.2s' }}>
              <Link href="/booking">
                <Button size="lg" className="h-14 px-8 rounded-2xl bg-primary hover:bg-primary/90 text-white text-lg shadow-xl shadow-blue-200/50 group">
                  Reservasi Online 
                  <ArrowRight className="ml-2 h-5 w-5 group-hover:translate-x-1 transition-transform" />
                </Button>
              </Link>
              <Link href="/menu">
                <Button size="lg" variant="outline" className="h-14 px-8 rounded-2xl text-lg border-blue-200 text-blue-700 hover:bg-blue-50">
                  Lihat Menu Menu
                </Button>
              </Link>
            </div>
          </div>
        </section>

        <section className="py-24 bg-white">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-16">
              <h2 className="text-3xl font-bold text-slate-900 mb-4">Fasilitas Premium</h2>
              <p className="text-slate-500">Dirancang khusus untuk kenyamanan dan produktivitas Anda.</p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <div className="glass p-8 rounded-3xl hover:-translate-y-2 transition-transform duration-300">
                <div className="w-14 h-14 bg-blue-100 rounded-2xl flex items-center justify-center text-primary mb-6">
                  <Coffee className="h-7 w-7" />
                </div>
                <h3 className="text-xl font-bold text-slate-900 mb-3">F&B Eksklusif</h3>
                <p className="text-slate-600 leading-relaxed">Nikmati beragam pilihan menu makanan dan minuman segar berkualitas yang disiapkan langsung oleh chef kami.</p>
              </div>
              <div className="glass p-8 rounded-3xl hover:-translate-y-2 transition-transform duration-300">
                <div className="w-14 h-14 bg-blue-100 rounded-2xl flex items-center justify-center text-primary mb-6">
                  <Clock className="h-7 w-7" />
                </div>
                <h3 className="text-xl font-bold text-slate-900 mb-3">Antrian Digital Cerdas</h3>
                <p className="text-slate-600 leading-relaxed">Sistem antrian real-time yang menjamin keadilan dan efisiensi waktu tunggu Anda selama berada di fasilitas.</p>
              </div>
              <div className="glass p-8 rounded-3xl hover:-translate-y-2 transition-transform duration-300">
                <div className="w-14 h-14 bg-blue-100 rounded-2xl flex items-center justify-center text-primary mb-6">
                  <ShieldCheck className="h-7 w-7" />
                </div>
                <h3 className="text-xl font-bold text-slate-900 mb-3">Privasi & Keamanan</h3>
                <p className="text-slate-600 leading-relaxed">Ruang tunggu tertutup dengan sistem keamanan terpadu, memberikan ketenangan maksimal sebelum aktivitas penerbangan.</p>
              </div>
            </div>
          </div>
        </section>
      </main>

      <footer className="bg-slate-900 text-slate-300 py-12 border-t border-slate-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 grid grid-cols-1 md:grid-cols-3 gap-8">
          <div>
            <div className="flex items-center gap-3 mb-6">
              <div className="w-8 h-8 bg-primary text-white rounded-lg flex items-center justify-center font-bold text-lg">
                A
              </div>
              <span className="font-bold text-xl text-white">Arjuna Lounge</span>
            </div>
            <p className="text-slate-400 text-sm leading-relaxed mb-4">
              Sistem Manajemen Lounge Terintegrasi — Balai Kesehatan Penerbangan, Kementerian Perhubungan.
            </p>
          </div>
          <div>
            <h4 className="text-white font-bold mb-4">Tautan</h4>
            <ul className="space-y-2 text-sm">
              <li><Link href="/booking" className="hover:text-primary transition-colors">Booking Online</Link></li>
              <li><Link href="/menu" className="hover:text-primary transition-colors">Digital Menu</Link></li>
              <li><Link href="/queue/display" className="hover:text-primary transition-colors">Status Antrian</Link></li>
            </ul>
          </div>
          <div>
            <h4 className="text-white font-bold mb-4">Kontak</h4>
            <ul className="space-y-3 text-sm text-slate-400">
              <li className="flex items-start gap-3">
                <MapPin className="h-5 w-5 text-primary shrink-0" />
                <span>Balai Kesehatan Penerbangan<br/>Kementerian Perhubungan RI</span>
              </li>
            </ul>
          </div>
        </div>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-12 pt-8 border-t border-slate-800 text-sm text-center text-slate-500">
          &copy; {new Date().getFullYear()} PT Pandawa Cipta Jaya. All rights reserved.
        </div>
      </footer>
    </div>
  );
}
