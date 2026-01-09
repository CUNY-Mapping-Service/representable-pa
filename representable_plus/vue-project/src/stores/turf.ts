import { defineStore } from "pinia";
import { ref, computed } from "vue";

export interface Turf {
    id: string;
    name: string;
    description: string;
    tracts: string[];
    createdAt: string;
}

export const useTurfStore = defineStore("turf", () => {
    const turfs = ref<Turf[]>([]);
    const selectedTurf = ref<Turf | null>(null);

    return { turfs, selectedTurf }
})