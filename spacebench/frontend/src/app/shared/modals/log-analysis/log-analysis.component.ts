import {Component, EventEmitter, Input, Output, OnInit} from '@angular/core';
import {CommonModule} from '@angular/common';
import {Analyse, RunLogsResponse} from '../../../interfaces/analysis.interface';
import {environment} from '../../../../environments/environment';
import {AnalysisService} from "../../../service/analysis.service";
import {FileService} from "../../../service/file.service";
import {LucideAngularModule} from "lucide-angular";

@Component({
    selector: 'app-log-analysis',
    standalone: true,
    imports: [CommonModule, LucideAngularModule],
    templateUrl: './log-analysis.component.html',
    styleUrls: ['./log-analysis.component.scss'],
})
export class LogAnalysisComponent implements OnInit {
    @Output() close = new EventEmitter<void>();
    @Input() comparisonInput: Analyse | null = null;

    constructor(private logService : AnalysisService, private fileService: FileService) {}

    analysis!: Analyse;
    logs: RunLogsResponse[] = [];
    statusColor = '#888';
    isCustomEstimator = false;

    loading = false;

    @Input({required: true}) set analysisInput(value: Analyse) {
        this.analysis = value;
        this.statusColor = ({'Terminé': '#4caf50', 'En cours': '#8bc34a', 'Échec': '#e05555'})[value.status] ?? '#888';
        this.isCustomEstimator = value.estimator_type === 'Plugin custom';
    }

    getLog(){
        this.logService.getLog(this.analysis.id).subscribe(data => {
            this.logs = data;
        });
    }

    ngOnInit(){
        this.getLog();

        if(this.comparisonInput){
            this.selectComparison(this.comparisonInput);
        }

        console.log(this.analysis);

    }

    downloadFile(fileId: string, type: string): void {

        this.fileService.download(fileId).subscribe(blob => {

            // Create fake click on a new <a>
            const a = document.createElement('a');
            a.href = window.URL.createObjectURL(blob);
            a.download = fileId+"."+type; // Add type debug. Better would to get the Content Disposition from CORS
            a.click();

            // Clean
            window.URL.revokeObjectURL(a.href);
        })
    }

    downloadAllFile(): void{

        const ids = [
            this.analysis.rinexFileId,
            this.analysis.gnssSp3FileId,
            this.analysis.clkFileId,
            this.analysis.estimatorFileId,
            ...(this.analysis.rsoFileIds ?? [])
        ].filter((id): id is string => !!id);

        if (!ids.length) {
            return;
        }

        this.loading = true;

        this.fileService.downloadBulk(ids).subscribe({
            next: (blob) => {
                const a = document.createElement('a');
                a.href = window.URL.createObjectURL(blob);
                a.download = this.analysis.name + '_files.zip';
                a.click();
                window.URL.revokeObjectURL(a.href);
                this.loading = false;
            },
            error: () => {
                this.loading = false;
            }
        });

    }


    // ══════════ COMPARISONS
    showConfig = true;
    showFiles = true;
    showResults = true;

    compareMode: 'off' | 'selecting' | 'comparing' = 'off';
    candidates: Analyse[] = [];
    candidatesLoading = false;

    comparisonAnalysis: Analyse | null = null;
    comparisonLogs: RunLogsResponse[] = [];
    comparisonStatusColor = '#888';
    comparisonIsCustomEstimator = false;


    startCompare(): void{
        this.compareMode = 'selecting';
        this.candidatesLoading = true;

        this.logService.getRuns(0, 500, true, 'created_at', 'desc', []).then(() => {
            this.candidates = this.logService.analysis.filter(a => a.id !== this.analysis.id && a.status === 'Terminé');
            this.candidatesLoading = false;
        })

    }

    selectComparison(a: Analyse): void{
        this.comparisonAnalysis = a;
        this.comparisonStatusColor = '#4caf50';
        this.comparisonIsCustomEstimator = a.estimator_type === 'Plugin custom';
        this.compareMode = 'comparing';

        this.logService.getLog(a.id).subscribe(data => {
            this.comparisonLogs = data;
        });
    }

    exitCompare(): void{
        this.compareMode = 'off';
        this.comparisonAnalysis = null;
        this.comparisonLogs = [];
    }
}
