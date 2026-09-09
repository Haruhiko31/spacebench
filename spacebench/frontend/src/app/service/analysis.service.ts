import {Injectable} from '@angular/core';
import {HttpClient} from '@angular/common/http';
import {firstValueFrom} from 'rxjs';
import {Analyse, RunResponse, RunLogsResponse} from '../interfaces/analysis.interface';
import {environment} from '../../environments/environment';


const MODELE_LABELS: Record<string, string> = {
    kinematic: 'Cinématique',
    dynamic: 'Dynamique',
    reduced_dynamic: 'Réduit-Dynamique',
};

const ESTIMATEUR_LABELS: Record<string, string> = {
    least_squares: 'Moindres carrés',
    kalman: 'Filtre de Kalman',
    custom: 'Plugin custom',
};

const STATUT_MAP: Record<string, Analyse['status']> = {
    pending: 'En cours',
    running: 'En cours',
    done: 'Terminé',
    failed: 'Échec',
};

@Injectable({providedIn: 'root'})
export class AnalysisService {

    analysis: Analyse[] = [];
    allAnalysis: Analyse[] = [];
    totalCount = 0;

    constructor(private http: HttpClient) {
    }

    async createRun(payload: {
        name: string;
        mission_name: string;
        mission_year: number;
        mission_day: number;
        orbital_model: string;
        estimator_type: string;
        rinex_file_id: string;
        gnss_sp3_file_id: string;
        gnss_clk_file_id: string;
        rso_file_ids: string[];
        estimator_file_id: string | null;
        max_iteration: number;
        tolerance: number;
    }) {
        await firstValueFrom(this.http.post(environment.apiUrl + '/api/runs', {
            ...payload,
            rms_3d: 0,
            rms_radial: 0,
            rms_along: 0,
            rms_cross: 0
        }))
    }

    // Backend format → Frontend human readable
    private mapRuns(runs: RunResponse[]): Analyse[] {
        return runs.map(r => ({
            id: r.id,
            name: r.name,
            mission_name: r.mission_name,
            mission_year: r.mission_year,
            mission_day: r.mission_day,
            orbital_model: MODELE_LABELS[r.orbital_model] ?? r.orbital_model,
            estimator_type: ESTIMATEUR_LABELS[r.estimator_type] ?? r.estimator_type,
            created_at: (r.created_at.slice(0, 16)).replace('T', ' '),
            status: STATUT_MAP[r.status] ?? 'En cours',
            max_iteration: r.max_iteration,
            tolerance: r.tolerance,
            rms_3d: r.rms_3d,
            rms_radial: r.rms_radial,
            rms_along: r.rms_along,
            rms_cross: r.rms_cross,
            gnssSp3FileId: r.gnss_sp3_file_id ?? undefined, // SP3 IGS
            rsoFileIds: r.rso_file_ids ?? undefined, // RSO MISSION
            rinexFileId: r.rinex_file_id ?? undefined, // RNX MISSION
            clkFileId: r.gnss_clk_file_id ?? undefined, // CLK IGS
            estimatorFileId: r.estimator_file_id ?? undefined,
        }));
    }

    // Get paginated data (for the datatable)
    async getRuns(skip = 0, limit = 10, fetchCount = false, sortBy = 'created_at', sortOrder = 'desc', statuses: string[] = []): Promise<void> {
        const statusParams = statuses.length ? '&' + statuses.map(s => `statuses=${encodeURIComponent(s)}`).join('&') : '';
        const runs = await firstValueFrom(this.http.get<RunResponse[]>(`${environment.apiUrl}/api/runs?skip=${skip}&limit=${limit}&sort_by=${sortBy}&sort_order=${sortOrder}${statusParams}`));

        if (fetchCount) {
            const countUrl = statuses.length
                ? `${environment.apiUrl}/api/runs/count?${statuses.map(s => `statuses=${encodeURIComponent(s)}`).join('&')}`
                : `${environment.apiUrl}/api/runs/count`;
            const countRes = await firstValueFrom(this.http.get<{ count: number }>(countUrl));
            this.totalCount = countRes.count;
        }
        console.log(runs);
        this.analysis = this.mapRuns(runs);
    }

    getLog(run_id: string){
        return this.http.get<RunLogsResponse[]>(`${environment.apiUrl}/api/runs/${run_id}/logs`);
    }


    // Get all the data (for histogram)
    async fetchAll(): Promise<void> {
        const countRes = await firstValueFrom(this.http.get<{ count: number }>(environment.apiUrl + '/api/runs/count'));
        const runs = await firstValueFrom(this.http.get<RunResponse[]>(environment.apiUrl + '/api/runs?skip=0&limit=' + countRes.count));
        this.allAnalysis = this.mapRuns(runs);
    }
}
