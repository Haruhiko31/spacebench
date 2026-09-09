import {Component, OnInit, ViewChild} from '@angular/core';
import {Router} from '@angular/router';
import {CommonModule} from '@angular/common';
import {NavbarComponent} from '../../shared/navbar/navbar.component';
import {AnalysisService} from '../../service/analysis.service';
import {Analyse} from '../../interfaces/analysis.interface';
import {HistogramComponent} from './histogram/histogram.component';
import {LucideAngularModule} from 'lucide-angular';
import {TooltipModule} from 'primeng/tooltip';
import {FilterMetadata} from 'primeng/api';
import {Table, TableLazyLoadEvent, TableModule} from 'primeng/table';
import {LogAnalysisComponent} from '../../shared/modals/log-analysis/log-analysis.component';
import {MultiSelectModule} from 'primeng/multiselect';
import {FormsModule} from "@angular/forms";

const PAR_PAGE = 5; // Number of row in datatable by default

interface Column {
    field: string;
    header: string;
}

@Component({
    selector: 'app-dashboard',
    standalone: true,
    imports: [CommonModule, NavbarComponent, HistogramComponent, LucideAngularModule,
        TooltipModule, TableModule, LogAnalysisComponent, MultiSelectModule, FormsModule],
    templateUrl: './dashboard.component.html',
    styleUrls: ['./dashboard.component.scss']
})
export class DashboardComponent implements OnInit {

    @ViewChild('dt') dt!: Table;
    @ViewChild(HistogramComponent) histogram!: HistogramComponent;


    showDatatable = true;
    showHistogram = true;
    sectionOverflow = 'visible';
    selectedAnalysis: Analyse | null = null;
    comparisonAnalysis: Analyse | null = null;

    selectedColumns!: Column[];
    selectedRows: Analyse[] = [];
    cols!: Column[];

    statusOptions = [
        {label: 'Terminé', value: 'done'},
        {label: 'En cours', value: 'pending'},
        {label: 'Échec', value: 'failed'},
    ];

    selectedStatuses: string[] = [];
    lastFilterKey = '';
    loading = false;
    totalRecords = 0;
    currentPageSize = PAR_PAGE;

    // Hide/Show histogram & Datatable
    toggleDatatable(): void {

        // 1 at least
        if (this.showDatatable && !this.showHistogram) {
            return;
        }

        this.showDatatable = !this.showDatatable;
    }

    toggleHistogram(): void {
        if (this.showHistogram && !this.showDatatable) {
            return;
        }
        this.showHistogram = !this.showHistogram;

        // Reset table to make it show 10 rows

        setTimeout(() => this.dt.reset());
    }

    constructor(
        public analysisService: AnalysisService,
        private router: Router
    ) {
    }

    ngOnInit(): void {

        // Show/Hide columns
        const visibleColumns = ['name', 'mission_name', 'mission_year', 'mission_day', 'orbital_model', 'estimator_type', 'created_at', 'status'];

        this.cols = [
            {field: 'id', header: 'ID'},
            {field: 'name', header: 'Nom'},
            {field: 'mission_name', header: 'Mission'},
            {field: 'mission_year', header: 'Année M'},
            {field: 'mission_day', header: 'Jour M'},
            {field: 'orbital_model', header: 'Modèle orbital'},
            {field: 'estimator_type', header: 'Estimateur'},
            {field: 'created_at', header: 'Date'},
            {field: 'status', header: 'Statut'},
            {field: 'rms_3d', header: '3D RMS'},
            {field: 'rms_along', header: 'RMS Along-Track'},
            {field: 'rms_cross', header: 'RMS Cross-Track'},
            {field: 'rms_radial', header: 'RMS Radial'}
        ];

        // Set default columns
        this.selectedColumns = this.cols.filter(col => visibleColumns.includes(col.field));
    }

    get analysis(): Analyse[] {
        return this.analysisService.analysis;
    }

    get parPage(): number {
        return (!this.showHistogram && this.showDatatable) ? 10 : PAR_PAGE;
    }

    onStatusFilterChange(): void {
        const filterKey = [...this.selectedStatuses].sort().join(',');
        if (filterKey !== this.lastFilterKey) {
            this.lastFilterKey = filterKey;
            this.totalRecords = 0; // forces count refetch on next lazyLoad
            this.dt.filter(this.selectedStatuses, 'status', 'in');
        }
    }

    lazyLoad(event: TableLazyLoadEvent): void {

        this.loading = true;

        const skip = event.first ?? 0;
        const limit = event.rows ?? PAR_PAGE;

        this.currentPageSize = limit;

        const sortBy = (event.sortField as string) || 'created_at';
        const sortOrder = event.sortOrder === 1 ? 'desc' : 'asc';

        const statuses = this.selectedStatuses ?? [];

        this.analysisService.getRuns(skip, limit, this.totalRecords === 0, sortBy, sortOrder, statuses).then(() => {
            this.totalRecords = this.analysisService.totalCount;
            this.loading = false;
        });
    }

    newAnalysis(): void {
        this.router.navigate(['/new-analysis']);
    }

    openLogs(a: Analyse): void {
        this.selectedAnalysis = a;
    }

    onColumnsChange(): void {
        this.selectedColumns = this.cols.filter(col =>
            this.selectedColumns.find(selectedCol => selectedCol.field === col.field)
        );
    }

    wideView = false;

    toggleViewWidth(): void {
        this.wideView = !this.wideView;
    }

    shownResults = false;

    // Add all the results cols to the shown columns.
    showResults(): void {

        const resultFields = ['rms_3d', 'rms_along', 'rms_cross', 'rms_radial'];
        const cols: Column[] = [];

        for (const field of resultFields) {
            const col = this.cols.find(c => c.field == field);

            if (col && !cols.includes(col)) {
                cols.push(col);
            }
        }

        if (!this.shownResults) {
            this.shownResults = true;

            for (const col of cols) {
                if (col) {
                    this.selectedColumns.push(col);
                }
            }

        } else {
            this.shownResults = false;

            for (const col of cols) {
                if (col) {
                    this.selectedColumns = this.selectedColumns.filter(c => c.field !== col.field);
                }
            }
        }

    }


    onSelectionChange(): void{
        console.log(this.selectedRows);
    }

    isSelected(id: string): boolean{
        return this.selectedRows.some(c => c.id == id);
    }

    showInHistogram(): void{

        // le rendre visible s'il ne l'est pas
        if(!this.showHistogram){
            this.showHistogram = true;
        }

        // filtrer sur les analyses sélectionnées
        setTimeout(() => {
            const names = this.selectedRows.map(a => a.name);
            this.histogram.highlightMissions(names);
        });
    }

    compareSelected(): void{
        if (this.selectedRows.length !== 2){ return; }

        this.selectedAnalysis = this.selectedRows[0];
        this.comparisonAnalysis = this.selectedRows[1];
    }

    allFinished(): boolean{

        let allFinished = true;

        for (const row of this.selectedRows){
            if (row['status'] !== 'Terminé'){
                allFinished = false;
            }
        }

        return allFinished;
    }

    get selectedRowsToString(){
        return this.selectedRows.map(a => a.name);
    }



}
