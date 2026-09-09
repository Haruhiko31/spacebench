import {Component, HostListener, ViewChild} from '@angular/core';
import {Router} from '@angular/router';
import {FormsModule, NgModel} from '@angular/forms';
import {CommonModule} from '@angular/common';
import {firstValueFrom} from 'rxjs';
import {FileService} from '../../service/file.service';
import {NavbarComponent} from '../../shared/navbar/navbar.component';
import {FileFormatsComponent} from '../../shared/modals/file-formats/file-formats.component';
import {BaseEstimatorComponent} from '../../shared/modals/base-estimator/base-estimator.component';
import {InputTextModule} from "primeng/inputtext";

import Swal from 'sweetalert2';
import {AnalysisService} from "../../service/analysis.service";
import {LucideAngularComponent, LucideAngularModule} from "lucide-angular";
import {TooltipModule} from "primeng/tooltip";

const MODELS = [
    {
        value: 'Cinématique',
        api: 'kinematic',
        description: 'Positions estimées indépendamment à chaque époque. Rapide, sans modèle de forces.',
        available: true
    },
    {
        value: 'Dynamique',
        api: 'dynamic',
        description: 'Propagation via les équations du mouvement. Plus précis, nécessite un modèle de forces complet.',
        available: false
    },
    {
        value: 'Réduit-Dynamique',
        api: 'reduced_dynamic',
        description: 'Hybride : dynamique simplifiée + corrections empiriques. Robuste aux erreurs de modélisation.',
        available: false
    },
];

const ESTIMATORS = [
    {
        value: 'Moindres carrés',
        api: 'BLSQ',
        description: "Ajustement batch sur l'arc complet.",
        available: true,
        custom: false
    },
    {
        value: 'Filtre de Kalman',
        api: 'KF',
        description: 'Estimation séquentielle époque par époque.',
        available: false,
        custom: false
    },
    {
        value: 'Extended Filtre de Kalman',
        api: 'EKF',
        description: 'Estimation séquentielle époque par époque.',
        available: false,
        custom: false
    },
    {
        value: 'Unscented Filtre de Kalman',
        api: 'UKF',
        description: 'Estimation séquentielle époque par époque.',
        available: false,
        custom: false
    },
    {
        value: 'Plugin custom',
        api: 'custom',
        description: 'Importez votre propre estimateur Python (.py) implémentant l\'interface BaseEstimator.',
        available: true,
        custom: true
    },
];

@Component({
    selector: 'app-new-analysis',
    standalone: true,
    imports: [CommonModule, FormsModule, NavbarComponent, FileFormatsComponent, BaseEstimatorComponent, InputTextModule, LucideAngularModule, TooltipModule],
    templateUrl: './new-analysis.component.html',
    styleUrls: ['./new-analysis.component.scss']
})
export class NewAnalysisComponent {

    step = 1;
    readonly stepTotal = 4; // const

    models = MODELS;
    estimators = ESTIMATORS;

    selectedModel = 'Cinématique'; // Default selected
    selectedEstimator = '';
    name = '';
    mission_name = '';

    mission_year: number = 0;
    mission_day: number = 0;

    RINEXFile: File | null = null;
    rinexId: string = '';

    gnssSP3File: File | null = null;
    gnssSP3Id: string = '';

    gnssCLKFile: File | null = null;
    gnssCLKId: string = '';

    rsoFiles: File[] = [];
    rsoIds: string[] = [];


    estimatorFile: File | null = null;
    estimatorId!: string;

    RINEXerror: string = '';
    gnssSP3error: string = '';
    gnssCLKerror: string = '';
    rsoError: string = '';
    estimatorError: string = '';

    showDocFiles = false;
    showDocEstimator = false;
    showDemoDropdown = false;

    availableMissionDays = [200,201,202,203,204,205,206,207,208,209,210,211,212,213,214,215,216,217,218,219,246];

    maxIter: number = 10;
    tolerance: number = 1e-4;


    doyToDate(doy: number, year: number) : string {
        const date = new Date(2010, 0, doy);
        const dd = String(date.getDate()).padStart(2, '0');
        const mm = String(date.getMonth() + 1).padStart(2, '0');
        return `${dd}-${mm}-${year}`;
    }


    @HostListener('document:click')
    closeDemoDropdown(): void {
        this.showDemoDropdown = false;
    }


    @ViewChild('fieldName') fieldName?: NgModel;

    loading = false;
    loading_validation = false;
    error = '';

    constructor(private fileService: FileService, private analysisService: AnalysisService, public router: Router) {
    }


    /* ════════ GETTERS ════════ */

    get rsoLabel(): string {
        return this.rsoFiles.map(f => f.name).join(', ');
    }


    /* ════════ File Extension Validation ════════ */

    private extension(f: File): string {
        return f.name.slice(f.name.lastIndexOf('.')).toLowerCase();
    }

    // ════════ IGS SP3
    async onGnssSP3File(event: Event): Promise<void> {
        const files = (event.target as HTMLInputElement).files;

        if (!files) return;

        try{
            for (const file of files) {
                if (this.extension(file) !== '.sp3') {
                    this.gnssSP3error = "Extension invalide « " + this.extension(file) + " » — fichier .sp3 attendu.";
                    this.gnssSP3File = null;
                    return;
                }

                this.gnssSP3error = '';
                this.gnssSP3File = file;
                this.gnssSP3Id = await this.uploadFile(this.gnssSP3File!);
            }
        }catch(e: any){
            this.gnssSP3error = e.error.detail ?? 'Error while validating the SP3 file.';
        }finally{
            this.loading_validation = false;
        }

    }

    // ════════ IGS CLOCK
    async onGnssCLKFile(event: Event): Promise<void> {

        const file = (event.target as HTMLInputElement).files?.[0];

        if (!file) return;

        try{
            const extension = this.extension(file);

            if (extension !== '.clk' && extension !== '.clk_30s') {
                this.gnssCLKerror = "Extension invalide « " + extension + " » — fichier .clk ou .clk_30s attendu.";
                this.gnssCLKFile = null;
                return;
            }

            this.gnssCLKerror = '';
            this.gnssCLKFile = file;
            this.gnssCLKId = await this.uploadFile(this.gnssCLKFile!);
        }catch(e: any){
            this.gnssCLKerror = e.error?.detail ?? 'Error while validating GNSS CLK File.';
        }finally{
            this.loading_validation = true;
        }

    }

    // ════════ RSO SP3
    async onRSOFiles(event: Event): Promise<void> {
        const files = Array.from((event.target as HTMLInputElement).files ?? []);

        if (!files.length) return;

        this.loading_validation = true;

        try{
            const invalid = files.find(f => this.extension(f) !== '.sp3');

            if (invalid) {
                this.rsoError = "Extension invalide « " + this.extension(invalid) + " » — fichiers .sp3 attendus.";
                this.rsoFiles = [];
                this.rsoIds = [];
                return;
            } else if (files.length > 2) {
                this.rsoError = 'Maximum 2 arcs SP3 pour l\'orbite de référence.';
                this.rsoFiles = [];
                this.rsoIds = [];
                return;
            } else {
                this.rsoError = '';
                this.rsoFiles = files;
            }

            this.rsoIds = [];

            for (const file of files){
                const rsoId = await this.uploadFile(file)
                this.rsoIds.push(rsoId)
            }
        }catch(e: any){
            this.rsoError = e.error.detail ?? 'Error while validating RSO File!';
        }finally{
            this.loading_validation = false;
        }


    }

    // ════════ RINEX
    async onRINEXFile(event: Event): Promise<void> {

        const file = (event.target as HTMLInputElement).files?.[0];

        if (!file) return;

        this.loading_validation = true;

        try{
            if (this.extension(file) !== '.rnx') {
                this.RINEXerror = "Extension invalide « " + this.extension(file) + " » — fichier .rnx attendu.";
                this.RINEXFile = null;
                this.rinexId = '';
                return;
            }

            this.RINEXerror = '';
            this.RINEXFile = file;
            this.rinexId = await this.uploadFile(this.RINEXFile!);
        }catch(e: any){
            this.RINEXerror = e.error.detail ?? 'Error while validating RINEX file';
        }finally{
            this.loading_validation = false;
        }
    }

    // ════════ ESTIMATOR
    async onEstimatorFile(event: Event): Promise<void> {
        const file = (event.target as HTMLInputElement).files?.[0];

        if (!file) return;

        if (this.extension(file) !== '.py') {
            this.estimatorError = "Extension invalide « " + this.extension(file) + " » — fichier .py attendu.";
            this.estimatorFile = null;
            return;
        }

        this.estimatorError = '';
        this.estimatorFile = file;

        if (this.selectedEstimator === 'Plugin custom' && this.estimatorFile) {
            this.estimatorId = await this.uploadFile(this.estimatorFile);
        }


    }


    /* ════════ HELPERS ════════ */
    showDocumentation(): void {
        this.showDocEstimator = true;
    }

    nextStep(): void {
        this.step++;
    }

    previousStep(): void {
        this.step--;
    }

    canContinue(): boolean {
        if (this.step === 1) {
            return !!this.rinexId && !this.RINEXerror &&
                !!this.gnssSP3Id && !this.gnssSP3error &&
                !!this.gnssCLKId && !this.gnssCLKerror &&
                this.rsoIds.length > 0 && !this.rsoError;
        }
        if (this.step === 2) return !!this.selectedModel;
        if (this.step === 3) {
            if (!this.selectedEstimator) return false;
            console.log(this.selectedEstimator);
            if (this.selectedEstimator === 'Plugin custom') return !!this.estimatorId;
            return true;
        }
        if (this.step === 4) return !!this.name.trim();
        return true;
    }

    private async uploadFile(file: File): Promise<string> {
        const res = await firstValueFrom(this.fileService.upload(file));
        return res.id;
    }

    // ════════ THIS STARTS THE ANALYSIS ════════ //

    async runAnalysis(): Promise<void> {

        this.fieldName?.control.markAsTouched();
        if (!this.canContinue()) return;
        this.loading = true;
        this.error = '';

        try {
            const model = MODELS.find(m => m.value === this.selectedModel)!;
            const estimator = ESTIMATORS.find(e => e.value === this.selectedEstimator)!;

            await this.analysisService.createRun({
                name: this.name.trim(),
                mission_name: this.mission_name.trim(),
                mission_year: this.mission_year,
                mission_day: this.mission_day,
                orbital_model: model.api,
                estimator_type: estimator.api,
                rinex_file_id: this.rinexId,
                gnss_sp3_file_id: this.gnssSP3Id,
                gnss_clk_file_id: this.gnssCLKId,
                rso_file_ids: this.rsoIds,
                estimator_file_id: this.selectedEstimator === 'Plugin custom' ? this.estimatorId : null,
                max_iteration: this.maxIter,
                tolerance: this.tolerance
            });


            await Swal.fire({
                icon: 'success',
                title: 'Mission lancée',
                text: "L'analyse « " + this.name.trim() + " » est en cours de traitement.",
                confirmButtonText: 'Voir le tableau de bord',
                background: '#111',
                color: '#fff',
                confirmButtonColor: '#4caf50',
            });

            this.router.navigate(['/dashboard']);

        } catch {
            this.error = 'Une erreur est survenue. Vérifiez que le backend est démarré.';
        } finally {
            this.loading = false;
        }
    }

    // ════════════ SEED DEMO DATA
    private async assetToFile(path: string, filename: string, type = 'application/octet-stream'): Promise<File> {
        const response = await fetch(path);
        if (!response.ok) {
            throw new Error(`Impossible de charger ${path}`);
        }

        const blob = await response.blob();
        return new File([blob], filename, { type });
    }

    // Convert a date to the RSO Filename format.
    // new Date(2010, 6, 19) { Mon Jul 19 2010 00:00:00 GMT+0200 (Central European Summer Time) } → 20100719
    private formatDateToMatchFile(date: Date): string {
        const y = date.getFullYear();
        const m = String(date.getMonth() + 1).padStart(2, '0');
        const dd = String(date.getDate()).padStart(2, '0');
        return `${y}${m}${dd}`
    }

    async populateDemoData(mission: string, day: number): Promise<void> {

        this.showDemoDropdown = false;
        this.loading_validation = true;

        this.error = '';

        try {

            // Mission == 'champ'

            // ═════════ RINEX

            const base = `/assets/test-files/missions/CHAMP/D${day}`;
            const RINEXFilename = `CH-OG-1-SST+2010_${day}_00_R.9.rnx`
            this.RINEXFile = await this.assetToFile(`${base}/GFZ/RINEX/${RINEXFilename}`, `${RINEXFilename}`)
            this.rinexId = await this.uploadFile(this.RINEXFile);

            // ═════════ RSO (ground truth)

            const date = new Date(2010, 0, day); // Date
            const nextDay = new Date(date)
            nextDay.setDate(date.getDate() + 1) // Date + 1
            const prevDay = new Date(date)
            prevDay.setDate(date.getDate() - 1) // Date - 1

            const rsoFilenames = [
                `GFZOP_RSO_L06_G_${this.formatDateToMatchFile(prevDay)}_220000_${this.formatDateToMatchFile(date)}_120030_v01.sp3`,
                `GFZOP_RSO_L06_G_${this.formatDateToMatchFile(date)}_100000_${this.formatDateToMatchFile(nextDay)}_000030_v01.sp3`
            ]

             console.log(rsoFilenames);

            this.rsoFiles = [
                await this.assetToFile(`${base}/GFZ/SP3/${rsoFilenames[0]}`, `${rsoFilenames[0]}`),
                await this.assetToFile(`${base}/GFZ/SP3/${rsoFilenames[1]}`, `${rsoFilenames[1]}`)
            ]

            this.rsoIds = [];

            for (const file of this.rsoFiles){
                this.rsoIds.push(await this.uploadFile(file));
            }

            const days = Math.floor(((date.getTime() - new Date(1980, 0, 6).getTime()) / (1000 * 60 * 60 * 24)));
            console.log("Days => ", days);
            const dow = (days+1) % 7;
            console.log("Dow => ", dow);

            let week = Math.floor((days / 7));

            // Passage à la week suivante.
            if((days % 7) == 6){
                week += 1;
            }

            console.log("Week => ", week);


            // ═════════ IGS SP3
            const gnssSP3Filename = `igs${week}${(dow)}.sp3`

             console.log("Filename  = ", `${base}/IGS/SP3/${gnssSP3Filename}`);

            this.gnssSP3File = await this.assetToFile(`${base}/IGS/SP3/${gnssSP3Filename}`, `${gnssSP3Filename}`)
            this.gnssSP3Id = await this.uploadFile(this.gnssSP3File);


            // ═════════ IGS CLK
            const gnssCLKFilename = `igs${week}${dow}.clk_30s`

            console.log("Filename  = ", gnssCLKFilename);

            this.gnssCLKFile = await this.assetToFile(`${base}/IGS/CLK/${gnssCLKFilename}`, `${gnssCLKFilename}`)
            this.gnssCLKId = await this.uploadFile(this.gnssCLKFile);


        } catch (e) {
            console.error(e);
            this.error = 'Impossible de charger les fichiers de démonstration.';
        } finally{
                this.loading_validation = false;
        }
    }
}
