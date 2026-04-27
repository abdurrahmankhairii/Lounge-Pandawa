"use client";

import { useQuery } from "@tanstack/react-query";
import api from "@/lib/axios";
import { useEffect, useState } from "react";
import { Users, UserCircle, Megaphone, Clock } from "lucide-react";
import { format } from "date-fns";
import { id } from "date-fns/locale";

interface QueueStatus {
  waiting_count: number;
  serving_count: number;
  current_ticket: string | null;
  next_tickets: string[];
}

export default function QueueDisplayBoard() {
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const { data: queue, isLoading } = useQuery({
    queryKey: ['queue_status_public'],
    queryFn: async () => {
      const res = await api.get<QueueStatus>('/queue/current');
      return res.data;
    },
    refetchInterval: 3000, // Poll every 3 seconds as requested
  });

  return (
    <div className="min-h-screen bg-slate-900 text-white overflow-hidden flex flex-col">
      {/* Header Bar */}
      <div className="h-24 bg-slate-950 flex items-center justify-between px-10 border-b border-slate-800 shadow-2xl z-10">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 bg-primary text-white rounded-xl flex items-center justify-center font-bold text-3xl shadow-lg shadow-blue-500/20">
            A
          </div>
          <div>
            <h1 className="font-bold text-3xl tracking-tight">Arjuna VIP Lounge</h1>
            <p className="text-slate-400 font-medium">Balai Kesehatan Penerbangan</p>
          </div>
        </div>
        <div className="text-right">
          <h2 className="text-4xl font-bold tracking-widest text-primary font-mono">{format(time, 'HH:mm:ss')}</h2>
          <p className="text-slate-400 font-medium">{format(time, 'EEEE, dd MMMM yyyy', { locale: id })}</p>
        </div>
      </div>

      <div className="flex-grow flex flex-col md:flex-row p-8 gap-8 relative">
        {/* Background Decorative */}
        <div className="absolute inset-0 bg-gradient-to-br from-blue-900/20 to-slate-900 z-0"></div>

        {/* Left Panel: Current Call */}
        <div className="flex-grow bg-slate-800/50 backdrop-blur-xl border border-slate-700/50 rounded-3xl p-10 flex flex-col items-center justify-center relative z-10 shadow-2xl">
          <div className="absolute top-10 right-10">
            <Megaphone className={`w-16 h-16 ${queue?.current_ticket ? 'text-green-400 animate-pulse' : 'text-slate-600'}`} />
          </div>
          
          <h3 className="text-4xl font-bold text-slate-400 mb-8 uppercase tracking-widest">Antrian Saat Ini</h3>
          
          <div className="relative">
            <div className={`w-[600px] h-[350px] rounded-[3rem] flex items-center justify-center border-4 shadow-2xl transition-all duration-500 ${queue?.current_ticket ? 'bg-primary/10 border-primary shadow-primary/20' : 'bg-slate-800/50 border-slate-700'}`}>
              {queue?.current_ticket ? (
                <span className="text-[12rem] font-black tracking-tighter text-white drop-shadow-xl animate-in zoom-in duration-500">
                  {queue.current_ticket}
                </span>
              ) : (
                <span className="text-5xl font-bold text-slate-600 uppercase tracking-widest">Menunggu...</span>
              )}
            </div>
            
            {/* Ping effect when there is a current ticket */}
            {queue?.current_ticket && (
              <div className="absolute inset-0 rounded-[3rem] border-4 border-primary animate-ping opacity-20 pointer-events-none"></div>
            )}
          </div>
        </div>

        {/* Right Panel: Upcoming Queue & Stats */}
        <div className="w-1/3 flex flex-col gap-8 relative z-10">
          
          {/* Next Queue List */}
          <div className="bg-slate-800/50 backdrop-blur-xl border border-slate-700/50 rounded-3xl p-8 shadow-2xl flex-grow flex flex-col">
            <h3 className="text-2xl font-bold text-slate-400 mb-8 flex items-center gap-3 border-b border-slate-700 pb-4 uppercase tracking-widest">
              <Clock className="w-8 h-8 text-blue-400" />
              Antrian Berikutnya
            </h3>
            
            <div className="flex-grow flex flex-col justify-center gap-6">
              {queue?.next_tickets.length === 0 ? (
                <div className="text-center text-slate-500 font-medium text-xl">
                  Tidak ada antrian berikutnya
                </div>
              ) : (
                queue?.next_tickets.map((ticket, index) => (
                  <div key={index} className="bg-slate-700/40 border border-slate-600/50 rounded-2xl p-6 flex items-center justify-between">
                    <span className="text-2xl font-bold text-slate-400">#{index + 1}</span>
                    <span className="text-5xl font-black text-white">{ticket}</span>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Stats Widget */}
          <div className="bg-slate-800/50 backdrop-blur-xl border border-slate-700/50 rounded-3xl p-8 shadow-2xl grid grid-cols-2 gap-4">
            <div className="text-center p-4 bg-slate-900/50 rounded-2xl">
              <Users className="w-10 h-10 text-amber-400 mx-auto mb-2" />
              <div className="text-5xl font-black text-white mb-1">{queue?.waiting_count || 0}</div>
              <div className="text-sm font-bold text-slate-400 uppercase tracking-wider">Menunggu</div>
            </div>
            <div className="text-center p-4 bg-slate-900/50 rounded-2xl">
              <UserCircle className="w-10 h-10 text-green-400 mx-auto mb-2" />
              <div className="text-5xl font-black text-white mb-1">{queue?.serving_count || 0}</div>
              <div className="text-sm font-bold text-slate-400 uppercase tracking-wider">Dilayani</div>
            </div>
          </div>

        </div>
      </div>
      
      {/* Ticker Bottom */}
      <div className="h-12 bg-primary/20 border-t border-primary/30 flex items-center overflow-hidden whitespace-nowrap">
        <div className="animate-marquee inline-block text-blue-200 font-medium tracking-widest text-lg">
          SELAMAT DATANG DI ARJUNA VIP LOUNGE • SILAKAN MENUJU RESEPSIONIS UNTUK CHECK-IN ATAU MELAKUKAN PEMESANAN OFFLINE • NIKMATI FASILITAS MAKANAN DAN MINUMAN YANG KAMI SEDIAKAN • HARAP MENUNGGU PANGGILAN ANTRIAN SESUAI DENGAN NOMOR ANDA
        </div>
      </div>

      <style jsx>{`
        @keyframes marquee {
          0% { transform: translateX(100vw); }
          100% { transform: translateX(-100%); }
        }
        .animate-marquee {
          animation: marquee 30s linear infinite;
        }
      `}</style>
    </div>
  );
}
