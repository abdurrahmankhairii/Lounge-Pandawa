"use client";

import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { format, addDays } from "date-fns";
import { id } from "date-fns/locale";
import api from "@/lib/axios";
import { useRouter } from "next/navigation";
import { useToast } from "@/hooks/use-toast";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Calendar, Clock, Loader2, ArrowLeft } from "lucide-react";
import Link from "next/link";

interface TimeSlot {
  id: number;
  slot_date: string;
  start_time: string;
  end_time: string;
  capacity: number;
  booked_count: number;
  available: number;
}

export default function BookingPage() {
  const router = useRouter();
  const { toast } = useToast();
  
  // States
  const [selectedDate, setSelectedDate] = useState<Date>(new Date());
  const [selectedSlot, setSelectedSlot] = useState<TimeSlot | null>(null);
  
  // Form State
  const [formData, setFormData] = useState({
    guest_name: "",
    guest_phone: "",
    guest_email: "",
    guest_type: "other",
    airline: "",
  });

  // Fetch Slots
  const { data: slots, isLoading: loadingSlots } = useQuery({
    queryKey: ['slots', format(selectedDate, 'yyyy-MM-dd')],
    queryFn: async () => {
      const res = await api.get<TimeSlot[]>(`/bookings/slots?target_date=${format(selectedDate, 'yyyy-MM-dd')}`);
      return res.data;
    }
  });

  // Create Booking Mutation
  const createBooking = useMutation({
    mutationFn: async (data: any) => {
      const res = await api.post('/bookings', data);
      return res.data;
    },
    onSuccess: (data) => {
      toast({ title: "Berhasil", description: "Booking berhasil dibuat!" });
      router.push(`/booking/confirm/${data.booking_code}`);
    },
    onError: (err: any) => {
      toast({
        title: "Gagal",
        description: err.response?.data?.detail || "Terjadi kesalahan",
        variant: "destructive"
      });
    }
  });

  // Handlers
  const handleDateChange = (daysToAdd: number) => {
    setSelectedDate(addDays(new Date(), daysToAdd));
    setSelectedSlot(null);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedSlot) return;
    
    createBooking.mutate({
      ...formData,
      slot_id: selectedSlot.id,
    });
  };

  return (
    <div className="min-h-screen bg-slate-50 py-10 px-4">
      <div className="max-w-4xl mx-auto">
        <Link href="/" className="inline-flex items-center text-slate-500 hover:text-primary mb-6 transition-colors">
          <ArrowLeft className="w-4 h-4 mr-2" />
          Kembali ke Beranda
        </Link>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* Left Column: Slots Selection */}
          <div className="space-y-6">
            <Card className="glass border-0 shadow-lg shadow-blue-100/50">
              <CardHeader>
                <CardTitle className="text-2xl text-slate-800">Pilih Jadwal</CardTitle>
                <CardDescription>Pilih tanggal dan waktu kunjungan Anda</CardDescription>
              </CardHeader>
              <CardContent>
                {/* Date Selector */}
                <div className="flex gap-2 mb-6 overflow-x-auto no-scrollbar pb-2">
                  {[0, 1, 2, 3, 4, 5, 6].map((offset) => {
                    const date = addDays(new Date(), offset);
                    const isSelected = format(date, 'yyyy-MM-dd') === format(selectedDate, 'yyyy-MM-dd');
                    return (
                      <button
                        key={offset}
                        onClick={() => handleDateChange(offset)}
                        className={`flex flex-col items-center justify-center min-w-[70px] h-20 rounded-2xl border transition-all ${
                          isSelected 
                            ? 'bg-primary border-primary text-white shadow-md shadow-blue-200' 
                            : 'bg-white border-slate-200 text-slate-600 hover:border-blue-300'
                        }`}
                      >
                        <span className="text-xs font-medium uppercase">{format(date, 'EEE', { locale: id })}</span>
                        <span className="text-xl font-bold">{format(date, 'd')}</span>
                      </button>
                    );
                  })}
                </div>

                {/* Slots Grid */}
                <div>
                  <h4 className="font-semibold text-slate-700 mb-4 flex items-center gap-2">
                    <Clock className="w-4 h-4 text-primary" />
                    Slot Tersedia
                  </h4>
                  {loadingSlots ? (
                    <div className="flex justify-center py-8">
                      <Loader2 className="w-8 h-8 animate-spin text-primary" />
                    </div>
                  ) : slots?.length === 0 ? (
                    <div className="text-center py-8 text-slate-500">Tidak ada slot tersedia untuk tanggal ini.</div>
                  ) : (
                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                      {slots?.map((slot) => {
                        const isSelected = selectedSlot?.id === slot.id;
                        const isFull = slot.available <= 0;
                        return (
                          <button
                            key={slot.id}
                            disabled={isFull}
                            onClick={() => setSelectedSlot(slot)}
                            className={`flex flex-col items-center justify-center p-3 rounded-xl border transition-all ${
                              isSelected 
                                ? 'bg-blue-50 border-primary text-primary ring-1 ring-primary' 
                                : isFull 
                                  ? 'bg-slate-100 border-slate-200 text-slate-400 cursor-not-allowed opacity-60' 
                                  : 'bg-white border-slate-200 text-slate-700 hover:border-blue-300 hover:shadow-sm'
                            }`}
                          >
                            <span className="font-bold text-sm">
                              {slot.start_time.substring(0, 5)} - {slot.end_time.substring(0, 5)}
                            </span>
                            <span className={`text-xs mt-1 ${isFull ? 'text-red-500 font-semibold' : 'text-slate-500'}`}>
                              {isFull ? 'Penuh' : `Sisa ${slot.available} kursi`}
                            </span>
                          </button>
                        );
                      })}
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Right Column: Form */}
          <div className="space-y-6">
            <Card className={`glass border-0 shadow-lg shadow-blue-100/50 transition-opacity duration-300 ${!selectedSlot ? 'opacity-50 pointer-events-none' : 'opacity-100'}`}>
              <CardHeader>
                <CardTitle className="text-2xl text-slate-800">Data Tamu</CardTitle>
                <CardDescription>
                  {selectedSlot 
                    ? `Booking untuk ${format(selectedDate, 'dd MMM yyyy', { locale: id })}, ${selectedSlot.start_time.substring(0,5)}` 
                    : "Pilih slot waktu terlebih dahulu"}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleSubmit} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="guest_name">Nama Lengkap</Label>
                    <Input 
                      id="guest_name" 
                      name="guest_name"
                      placeholder="Masukkan nama sesuai identitas" 
                      required
                      value={formData.guest_name}
                      onChange={handleInputChange}
                      className="rounded-xl border-slate-200 focus-visible:ring-primary"
                    />
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="guest_phone">No. Handphone (WA)</Label>
                      <Input 
                        id="guest_phone" 
                        name="guest_phone"
                        placeholder="0812xxx" 
                        required
                        value={formData.guest_phone}
                        onChange={handleInputChange}
                        className="rounded-xl border-slate-200 focus-visible:ring-primary"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="guest_email">Email</Label>
                      <Input 
                        id="guest_email" 
                        name="guest_email"
                        type="email"
                        placeholder="email@example.com" 
                        required
                        value={formData.guest_email}
                        onChange={handleInputChange}
                        className="rounded-xl border-slate-200 focus-visible:ring-primary"
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="guest_type">Tipe Tamu</Label>
                    <select 
                      id="guest_type" 
                      name="guest_type"
                      required
                      value={formData.guest_type}
                      onChange={handleInputChange}
                      className="flex h-10 w-full rounded-xl border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
                    >
                      <option value="pilot">Pilot</option>
                      <option value="cabin_crew">Cabin Crew</option>
                      <option value="medcheck">Peserta Medical Check-up</option>
                      <option value="other">Lainnya</option>
                    </select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="airline">Maskapai / Instansi (Opsional)</Label>
                    <Input 
                      id="airline" 
                      name="airline"
                      placeholder="Garuda Indonesia, Lion Air, dll" 
                      value={formData.airline}
                      onChange={handleInputChange}
                      className="rounded-xl border-slate-200 focus-visible:ring-primary"
                    />
                  </div>

                  <Button 
                    type="submit" 
                    className="w-full h-12 rounded-xl text-md font-semibold mt-4 shadow-md shadow-blue-200 hover:shadow-lg transition-all"
                    disabled={!selectedSlot || createBooking.isPending}
                  >
                    {createBooking.isPending ? (
                      <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Memproses...</>
                    ) : (
                      "Konfirmasi Booking"
                    )}
                  </Button>
                </form>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
