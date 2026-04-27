"use client";

import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import api from "@/lib/axios";
import { useToast } from "@/hooks/use-toast";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Loader2, Users, UserCheck, AlertTriangle } from "lucide-react";

export default function WalkInPage() {
  const { toast } = useToast();
  
  const [formData, setFormData] = useState({
    guest_name: "",
    guest_phone: "",
    guest_type: "other",
    airline: "",
    notes: "",
  });

  const { data: capacity, isLoading: loadingCapacity, refetch: refetchCapacity } = useQuery({
    queryKey: ['capacity_status'],
    queryFn: async () => {
      const res = await api.get('/staff/capacity');
      return res.data;
    },
    refetchInterval: 30000, // Refresh every 30s
  });

  const createWalkin = useMutation({
    mutationFn: async (data: any) => {
      const res = await api.post('/staff/bookings/walkin', data);
      return res.data;
    },
    onSuccess: (data) => {
      toast({ 
        title: "Walk-in Berhasil", 
        description: `Nomor Antrian: ${data.queue_ticket.ticket_number}` 
      });
      setFormData({ guest_name: "", guest_phone: "", guest_type: "other", airline: "", notes: "" });
      refetchCapacity();
      // Optionally print ticket logic here
    },
    onError: (err: any) => {
      toast({
        title: "Gagal",
        description: err.response?.data?.detail || "Terjadi kesalahan",
        variant: "destructive"
      });
    }
  });

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    createWalkin.mutate(formData);
  };

  const isNearingCapacity = capacity?.occupancy_rate > 80;
  const isFull = capacity?.available <= 0;

  return (
    <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
      {/* Form Section */}
      <div className="xl:col-span-2">
        <Card className="border-0 shadow-lg shadow-blue-100/40 rounded-2xl overflow-hidden">
          <div className="h-2 bg-primary w-full"></div>
          <CardHeader className="bg-white pb-4 border-b border-slate-100">
            <CardTitle className="text-2xl text-slate-800">Registrasi Tamu Walk-in</CardTitle>
            <CardDescription>
              Masukkan data tamu yang datang langsung ke lounge tanpa reservasi online.
            </CardDescription>
          </CardHeader>
          <CardContent className="bg-white pt-6">
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <Label htmlFor="guest_name">Nama Lengkap <span className="text-red-500">*</span></Label>
                  <Input 
                    id="guest_name" 
                    name="guest_name"
                    required
                    value={formData.guest_name}
                    onChange={handleInputChange}
                    className="h-12 rounded-xl bg-slate-50 border-slate-200"
                    placeholder="Sesuai identitas"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="guest_phone">No. Handphone</Label>
                  <Input 
                    id="guest_phone" 
                    name="guest_phone"
                    value={formData.guest_phone}
                    onChange={handleInputChange}
                    className="h-12 rounded-xl bg-slate-50 border-slate-200"
                    placeholder="0812xxxx"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="guest_type">Tipe Tamu <span className="text-red-500">*</span></Label>
                  <select 
                    id="guest_type" 
                    name="guest_type"
                    required
                    value={formData.guest_type}
                    onChange={handleInputChange}
                    className="flex h-12 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                  >
                    <option value="pilot">Pilot</option>
                    <option value="cabin_crew">Cabin Crew</option>
                    <option value="medcheck">Peserta Medical Check-up</option>
                    <option value="other">Lainnya</option>
                  </select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="airline">Maskapai / Instansi</Label>
                  <Input 
                    id="airline" 
                    name="airline"
                    value={formData.airline}
                    onChange={handleInputChange}
                    className="h-12 rounded-xl bg-slate-50 border-slate-200"
                    placeholder="Garuda, Lion, dll"
                  />
                </div>
                <div className="col-span-1 md:col-span-2 space-y-2">
                  <Label htmlFor="notes">Catatan Khusus (Alergi, dll)</Label>
                  <Input 
                    id="notes" 
                    name="notes"
                    value={formData.notes}
                    onChange={handleInputChange}
                    className="h-12 rounded-xl bg-slate-50 border-slate-200"
                    placeholder="Opsional"
                  />
                </div>
              </div>

              <div className="pt-4 border-t border-slate-100 flex items-center justify-between">
                <p className="text-sm text-slate-500">
                  Status otomatis akan menjadi <strong>Checked-in</strong> setelah submit.
                </p>
                <Button 
                  type="submit" 
                  disabled={isFull || createWalkin.isPending}
                  className="h-12 px-8 rounded-xl font-bold shadow-lg shadow-primary/20"
                >
                  {createWalkin.isPending ? <Loader2 className="w-5 h-5 animate-spin mr-2" /> : <UserCheck className="w-5 h-5 mr-2" />}
                  Check-in & Generate Antrian
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>

      {/* Sidebar Section */}
      <div className="space-y-6">
        <Card className={`border-0 shadow-lg rounded-2xl overflow-hidden transition-all duration-300 ${isFull ? 'bg-red-50' : isNearingCapacity ? 'bg-amber-50' : 'bg-white'}`}>
          <CardHeader className="pb-2">
            <CardTitle className="text-lg flex items-center justify-between text-slate-800">
              Kapasitas Saat Ini
              <Users className={`w-5 h-5 ${isFull ? 'text-red-500' : isNearingCapacity ? 'text-amber-500' : 'text-primary'}`} />
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loadingCapacity ? (
              <div className="flex justify-center py-6"><Loader2 className="w-6 h-6 animate-spin text-primary" /></div>
            ) : (
              <div>
                <div className="flex items-end justify-between mb-2">
                  <span className="text-5xl font-black tracking-tighter text-slate-900">{capacity?.occupied || 0}</span>
                  <span className="text-slate-500 font-medium mb-1">/ {capacity?.total_capacity || 0} Kursi</span>
                </div>
                
                {/* Progress Bar */}
                <div className="h-3 w-full bg-slate-200 rounded-full overflow-hidden mt-4">
                  <div 
                    className={`h-full transition-all duration-1000 ease-out ${isFull ? 'bg-red-500' : isNearingCapacity ? 'bg-amber-500' : 'bg-primary'}`}
                    style={{ width: `${capacity?.occupancy_rate || 0}%` }}
                  ></div>
                </div>
                
                <div className="flex justify-between mt-3 text-sm font-medium">
                  <span className="text-slate-500">Tersedia: <span className="text-slate-800">{capacity?.available || 0}</span></span>
                  <span className={`${isFull ? 'text-red-600' : isNearingCapacity ? 'text-amber-600' : 'text-primary'}`}>
                    {capacity?.occupancy_rate || 0}% Terisi
                  </span>
                </div>

                {isFull && (
                  <div className="mt-6 p-4 bg-red-100 text-red-700 rounded-xl flex items-start gap-3 border border-red-200">
                    <AlertTriangle className="w-5 h-5 shrink-0 mt-0.5" />
                    <div>
                      <h4 className="font-bold text-sm">Lounge Penuh</h4>
                      <p className="text-xs mt-1">Tidak dapat menerima tamu walk-in saat ini. Arahkan tamu ke area waiting list di luar.</p>
                    </div>
                  </div>
                )}
                
                {!isFull && isNearingCapacity && (
                  <div className="mt-6 p-4 bg-amber-100 text-amber-700 rounded-xl flex items-start gap-3 border border-amber-200">
                    <AlertTriangle className="w-5 h-5 shrink-0 mt-0.5" />
                    <div>
                      <h4 className="font-bold text-sm">Kapasitas Hampir Penuh</h4>
                      <p className="text-xs mt-1">Harap perhatikan ketersediaan kursi fisik di dalam lounge.</p>
                    </div>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
