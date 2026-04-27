"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import { format } from "date-fns";
import { id } from "date-fns/locale";
import api from "@/lib/axios";
import { QRCodeSVG } from "qrcode.react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Loader2, CheckCircle2, Download, CalendarPlus, ChevronRight } from "lucide-react";
import Link from "next/link";

export default function BookingConfirmPage() {
  const params = useParams();
  const code = params.code as string;

  const { data: booking, isLoading } = useQuery({
    queryKey: ['booking', code],
    queryFn: async () => {
      const res = await api.get(`/bookings/${code}`);
      return res.data;
    },
    enabled: !!code,
  });

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <Loader2 className="w-10 h-10 animate-spin text-primary" />
      </div>
    );
  }

  if (!booking) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-slate-50 p-4 text-center">
        <div className="w-16 h-16 bg-red-100 text-red-500 rounded-full flex items-center justify-center mb-4">
          <span className="text-2xl font-bold">!</span>
        </div>
        <h1 className="text-2xl font-bold text-slate-800 mb-2">Booking Tidak Ditemukan</h1>
        <p className="text-slate-500 mb-6">Kode booking {code} tidak valid atau tidak ditemukan.</p>
        <Link href="/booking">
          <Button>Kembali ke Halaman Booking</Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 py-10 px-4 flex justify-center">
      <div className="w-full max-w-lg">
        <Card className="border-0 shadow-2xl shadow-blue-100/60 overflow-hidden relative">
          {/* Decorative Top Banner */}
          <div className="h-32 bg-gradient-to-r from-blue-500 to-primary absolute top-0 left-0 right-0 z-0 flex items-center justify-center">
            <div className="absolute inset-0 bg-white/10" style={{ backgroundImage: 'radial-gradient(circle at 2px 2px, rgba(255,255,255,0.15) 1px, transparent 0)', backgroundSize: '16px 16px' }}></div>
          </div>
          
          <CardHeader className="relative z-10 pt-8 pb-16 text-center text-white">
            <div className="w-16 h-16 bg-white rounded-full flex items-center justify-center mx-auto mb-4 shadow-lg text-green-500">
              <CheckCircle2 className="w-10 h-10" />
            </div>
            <CardTitle className="text-2xl font-bold text-white">Booking Terkonfirmasi</CardTitle>
            <CardDescription className="text-blue-100 text-md">
              Terima kasih, {booking.guest_name}. Reservasi Anda berhasil.
            </CardDescription>
          </CardHeader>

          <CardContent className="relative z-10 bg-white pt-8 px-8 rounded-t-3xl -mt-8">
            <div className="flex justify-center mb-8">
              <div className="p-4 bg-white rounded-2xl shadow-lg border border-slate-100 inline-block">
                <QRCodeSVG 
                  value={booking.booking_code} 
                  size={200}
                  level="Q"
                  includeMargin={false}
                  imageSettings={{
                    src: "/favicon.ico", // Or logo URL
                    x: undefined,
                    y: undefined,
                    height: 24,
                    width: 24,
                    excavate: true,
                  }}
                />
                <div className="text-center mt-4 font-mono font-bold tracking-widest text-lg text-slate-800">
                  {booking.booking_code}
                </div>
              </div>
            </div>

            <div className="space-y-4 mb-8">
              <div className="grid grid-cols-2 gap-4 pb-4 border-b border-slate-100">
                <div>
                  <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Tanggal</p>
                  <p className="font-semibold text-slate-800">
                    {format(new Date(booking.slot.slot_date), 'dd MMMM yyyy', { locale: id })}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Waktu</p>
                  <p className="font-semibold text-slate-800">
                    {booking.slot.start_time.substring(0,5)} - {booking.slot.end_time.substring(0,5)} WIB
                  </p>
                </div>
              </div>

              <div className="pb-4 border-b border-slate-100">
                <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Data Tamu</p>
                <p className="font-semibold text-slate-800">{booking.guest_name}</p>
                <p className="text-sm text-slate-600">{booking.guest_phone} • {booking.guest_email}</p>
                {booking.airline && <p className="text-sm text-slate-600 mt-1">{booking.airline}</p>}
              </div>

              <div>
                <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Status</p>
                <div className="inline-flex items-center px-3 py-1 rounded-full bg-green-100 text-green-700 text-xs font-bold uppercase tracking-wider">
                  {booking.status}
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-3">
              <Button variant="outline" className="w-full h-12 rounded-xl border-slate-200 text-slate-700 hover:bg-slate-50">
                <CalendarPlus className="w-5 h-5 mr-2" />
                Tambah ke Kalender
              </Button>
              <Button variant="outline" className="w-full h-12 rounded-xl border-slate-200 text-slate-700 hover:bg-slate-50">
                <Download className="w-5 h-5 mr-2" />
                Unduh Tiket
              </Button>
            </div>
          </CardContent>
          
          <div className="bg-slate-50 p-6 text-center border-t border-slate-100">
            <p className="text-sm text-slate-500 mb-4">
              Tunjukkan QR Code ini kepada resepsionis lounge saat Anda tiba untuk proses check-in.
            </p>
            <Link href="/" className="inline-flex items-center text-primary font-semibold hover:text-blue-700 transition-colors">
              Kembali ke Beranda <ChevronRight className="w-4 h-4 ml-1" />
            </Link>
          </div>
        </Card>
      </div>
    </div>
  );
}
