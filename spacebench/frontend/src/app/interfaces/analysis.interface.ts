export interface Analyse {
    id: string;
    name: string;
    mission_name: string;
    mission_year: number;
    mission_day: number;
    orbital_model: string;
    estimator_type: string;
    created_at: string;
    status: 'Terminé' | 'En cours' | 'Échec';
    //metrics?: Metriques;
    max_iteration: number;
    tolerance: number;
    rms_3d: number | null;
    rms_radial: number | null;
    rms_along: number | null;
    rms_cross: number | null;
    sp3FileId?: string;
    rinexFileId?: string;
    gnssSp3FileId?: string;
    rsoFileIds?: string[];
    clkFileId?: string;
    estimatorFileId?: string;
}

export interface RunResponse {
    id: string;
    name: string;
    mission_name: string;
    mission_year: number;
    mission_day: number;
    orbital_model: string;
    estimator_type: string;
    status: string;
    created_at: string;
    gnss_sp3_file_id: string | null;
    gnss_clk_file_id: string | null;
    rinex_file_id: string | null;
    rso_file_ids: string[] | null;
    estimator_file_id: string | null;
    max_iteration: number;
    tolerance: number;
    rms_3d: number | null;
    rms_radial: number | null;
    rms_along: number | null;
    rms_cross: number | null;
}

export interface RunLogsResponse {
    run_id: string
    level: string
    phase: string
    created_at: string
    message: string
}



