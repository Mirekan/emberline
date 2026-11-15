export const PRESET_NAMES: Record<"id" | "en", Record<string, string>> = {
  id: {
    riau: "Riau (Lahan Gambut Sumatera)",
    central_kalimantan: "Kalimantan Tengah (Eks-PLG)",
    south_sumatra: "Sumatera Selatan (Ogan Komering Ilir)",
    jambi: "Jambi (Gambut & Perkebunan)",
    merauke: "Papua Selatan (Merauke)",
    kalbar: "Kalimantan Barat (Kubu Raya & Ketapang)",
    kaltim: "Kalimantan Timur (DAS Mahakam & Pesisir)",
    papua_selatan: "Papua Selatan (Mappi & Asmat)",
    sulsel: "Sulawesi Selatan (Sabana & Pertanian)",
    ntt: "Nusa Tenggara Timur (Sabana Musiman)",
    ntb: "Nusa Tenggara Barat (Sumbawa & Lombok)",
    sumut_aceh: "Sumatera Utara & Aceh (Pesisir Timur)",
    lampung: "Lampung (Perkebunan & Transmigrasi)",
    papua_barat: "Papua Barat (Kepala Burung)",
    maluku: "Maluku (Halmahera & Seram)",
    jawa: "Pulau Jawa (Pesisir & Lahan Basah)",
    bengkulu_barat: "Bengkulu & Sumbar (Pesisir Barat)",
  },
  en: {
    riau: "Riau (Sumatra Peatland)",
    central_kalimantan: "Central Kalimantan (Ex-Mega Rice Project)",
    south_sumatra: "South Sumatra (Ogan Komering Ilir)",
    jambi: "Jambi (Peat & Plantation)",
    merauke: "Merauke (Papua Seasonal Savanna)",
    kalbar: "West Kalimantan (Kubu Raya & Ketapang)",
    kaltim: "East/North Kalimantan (Mahakam & Coast)",
    papua_selatan: "South Papua (Mappi & Asmat)",
    sulsel: "South Sulawesi (Savanna & Agricultural)",
    ntt: "East Nusa Tenggara (Seasonal Savanna)",
    ntb: "West Nusa Tenggara (Sumbawa & Lombok)",
    sumut_aceh: "North Sumatra & Aceh (East Coast Peatland)",
    lampung: "Lampung (Plantation & Agriculture)",
    papua_barat: "West Papua (Bird's Head)",
    maluku: "Maluku (Halmahera & Seram)",
    jawa: "Java Island (Wetland & Coastal)",
    bengkulu_barat: "Bengkulu & West Sumatra (West Coast)",
  },
};

export type ProvinceEntry = {
  name: string;
  preset: string;
  island: string;
  islandEn: string;
};

export const PROVINCES_38: ProvinceEntry[] = [
  // Sumatera
  { name: "Aceh", preset: "sumut_aceh", island: "Sumatera", islandEn: "Sumatra" },
  { name: "Sumatera Utara", preset: "sumut_aceh", island: "Sumatera", islandEn: "Sumatra" },
  { name: "Sumatera Barat", preset: "bengkulu_barat", island: "Sumatera", islandEn: "Sumatra" },
  { name: "Riau", preset: "riau", island: "Sumatera", islandEn: "Sumatra" },
  { name: "Kepulauan Riau", preset: "riau", island: "Sumatera", islandEn: "Sumatra" },
  { name: "Jambi", preset: "jambi", island: "Sumatera", islandEn: "Sumatra" },
  { name: "Sumatera Selatan", preset: "south_sumatra", island: "Sumatera", islandEn: "Sumatra" },
  { name: "Kepulauan Bangka Belitung", preset: "south_sumatra", island: "Sumatera", islandEn: "Sumatra" },
  { name: "Bengkulu", preset: "bengkulu_barat", island: "Sumatera", islandEn: "Sumatra" },
  { name: "Lampung", preset: "lampung", island: "Sumatera", islandEn: "Sumatra" },

  // Jawa
  { name: "Banten", preset: "jawa", island: "Jawa", islandEn: "Java" },
  { name: "DKI Jakarta", preset: "jawa", island: "Jawa", islandEn: "Java" },
  { name: "Jawa Barat", preset: "jawa", island: "Jawa", islandEn: "Java" },
  { name: "Jawa Tengah", preset: "jawa", island: "Jawa", islandEn: "Java" },
  { name: "DI Yogyakarta", preset: "jawa", island: "Jawa", islandEn: "Java" },
  { name: "Jawa Timur", preset: "jawa", island: "Jawa", islandEn: "Java" },

  // Bali & Nusa Tenggara
  { name: "Bali", preset: "ntb", island: "Bali & Nusa Tenggara", islandEn: "Lesser Sunda Islands" },
  { name: "Nusa Tenggara Barat", preset: "ntb", island: "Bali & Nusa Tenggara", islandEn: "Lesser Sunda Islands" },
  { name: "Nusa Tenggara Timur", preset: "ntt", island: "Bali & Nusa Tenggara", islandEn: "Lesser Sunda Islands" },

  // Kalimantan
  { name: "Kalimantan Barat", preset: "kalbar", island: "Kalimantan", islandEn: "Borneo" },
  { name: "Kalimantan Tengah", preset: "central_kalimantan", island: "Kalimantan", islandEn: "Borneo" },
  { name: "Kalimantan Selatan", preset: "central_kalimantan", island: "Kalimantan", islandEn: "Borneo" },
  { name: "Kalimantan Timur", preset: "kaltim", island: "Kalimantan", islandEn: "Borneo" },
  { name: "Kalimantan Utara", preset: "kaltim", island: "Kalimantan", islandEn: "Borneo" },

  // Sulawesi
  { name: "Sulawesi Utara", preset: "sulsel", island: "Sulawesi", islandEn: "Sulawesi" },
  { name: "Gorontalo", preset: "sulsel", island: "Sulawesi", islandEn: "Sulawesi" },
  { name: "Sulawesi Tengah", preset: "sulsel", island: "Sulawesi", islandEn: "Sulawesi" },
  { name: "Sulawesi Barat", preset: "sulsel", island: "Sulawesi", islandEn: "Sulawesi" },
  { name: "Sulawesi Selatan", preset: "sulsel", island: "Sulawesi", islandEn: "Sulawesi" },
  { name: "Sulawesi Tenggara", preset: "sulsel", island: "Sulawesi", islandEn: "Sulawesi" },

  // Maluku
  { name: "Maluku", preset: "maluku", island: "Kepulauan Maluku", islandEn: "Maluku Islands" },
  { name: "Maluku Utara", preset: "maluku", island: "Kepulauan Maluku", islandEn: "Maluku Islands" },

  // Papua
  { name: "Papua", preset: "merauke", island: "Papua", islandEn: "Papua" },
  { name: "Papua Barat", preset: "papua_barat", island: "Papua", islandEn: "Papua" },
  { name: "Papua Barat Daya", preset: "papua_barat", island: "Papua", islandEn: "Papua" },
  { name: "Papua Tengah", preset: "merauke", island: "Papua", islandEn: "Papua" },
  { name: "Papua Pegunungan", preset: "merauke", island: "Papua", islandEn: "Papua" },
  { name: "Papua Selatan", preset: "papua_selatan", island: "Papua", islandEn: "Papua" },
];
