import {Component, OnInit, OnDestroy, ElementRef, ViewChild, HostListener, Input, SimpleChanges, OnChanges} from '@angular/core';
import {CommonModule} from '@angular/common';
import {FormsModule} from '@angular/forms';
import {
    Chart, BarController, BarElement, CategoryScale, LinearScale, Tooltip,
    type Plugin, type ChartEvent, type ActiveElement,
} from 'chart.js';
import {AnalysisService} from '../../../service/analysis.service';
import {Analyse} from '../../../interfaces/analysis.interface';
import {LucideAngularModule} from "lucide-angular";
import {TooltipModule} from "primeng/tooltip";

Chart.register(BarController, BarElement, CategoryScale, LinearScale, Tooltip);

type Metric = 'rms_3d' | 'rms_radial' | 'rms_along' | 'rms_cross';

const METRICS: { key: Metric; label: string }[] = [
    {key: 'rms_3d', label: '3D RMS'},
    {key: 'rms_radial', label: 'Radial'},
    {key: 'rms_along', label: 'Along-track'},
    {key: 'rms_cross', label: 'Cross-track'},
];

const LIMITS: { value: number; label: string }[] = [
    {value: 5, label: '5'},
    {value: 10, label: '10'},
    {value: 20, label: '20'},
];

const MAX_ANALYSIS = 300;

function drawLine(ctx: CanvasRenderingContext2D, left: number, right: number, y: number, couleur: string): void {
    ctx.save();
    ctx.beginPath();
    ctx.setLineDash([4, 5]);
    ctx.moveTo(left, y);
    ctx.lineTo(right, y);
    ctx.strokeStyle = couleur;
    ctx.lineWidth = 1;
    ctx.stroke();
    ctx.restore();
}


const lineHover: Plugin<'bar'> = {
    id: 'lineHover',

    afterDraw(chart) {
        const { ctx, chartArea, data, scales } = chart;
        const { left, right } = chartArea;

        const pinnedIndex = (chart as any)._epingleIdx as number | null;
        const dataset = data.datasets[0].data as number[];

        if (pinnedIndex !== null && pinnedIndex < dataset.length) {
            const value = dataset[pinnedIndex];
            const y = scales['y'].getPixelForValue(value);

            drawLine(ctx, left, right, y, 'rgba(255, 255, 255, 0.7)');

            const meta = chart.getDatasetMeta(0);
            const bar = meta.data[pinnedIndex] as any;

            const x = bar.x;
            const top = bar.y;
            const height = bar.base - bar.y;

            ctx.save();
            ctx.font = 'bold 11px sans-serif';
            ctx.fillStyle = 'rgba(255, 255, 255, 0.9)';
            ctx.textAlign = 'center';
            ctx.textBaseline = height > 22 ? 'top' : 'bottom';
            ctx.fillText(`${value} cm`, x, height > 22 ? top + 5 : top - 4);
            ctx.restore();
        }

        const active = chart.getActiveElements()[0];
        if (!active || active.index === pinnedIndex) return;

        const hoverValue = dataset[active.index];
        const hoverY = scales['y'].getPixelForValue(hoverValue);

        drawLine(ctx, left, right, hoverY, 'rgba(255, 255, 255, 0.35)');
    },
};
@Component({
    selector: 'app-histogram',
    standalone: true,
    imports: [CommonModule, FormsModule, LucideAngularModule, TooltipModule],
    templateUrl: './histogram.component.html',
    styleUrls: ['./histogram.component.scss']
})
export class HistogramComponent implements OnInit, OnDestroy, OnChanges {
    @Input() extended = false;
    @Input() selectedNames: string[] = [];

    @ViewChild('canvas', {static: true}) canvasRef!: ElementRef<HTMLCanvasElement>;

    metrics = METRICS;
    limits = LIMITS;
    readonly maxAnalysis = MAX_ANALYSIS;

    activeMetrics: Metric = 'rms_3d';
    activeLimit: number = 5;

    customInputValue: number | null = null;
    customLimitExceeded = false;

    dropdownOpen = false;
    visibleAnalysisCount = 50;
    selectedMission = new Set<string>();
    private _search = '';
    modelFilter = '';
    estimatorFilter = '';

    allTheData: Analyse[] = [];
    private originalData: Analyse[] = [];
    private tempVisible: Analyse[] = [];
    filteredDatas: Analyse[] = [];
    private chart!: Chart<'bar', number[], string>;

    sortIcon = 'arrow-down-up'; // arrow-down-1-0 DESC && arrow-up-1-0 ASC
    dataSortIcon = 'arrow-down-up'; // arrow-down-1-0 DESC && arrow-up-1-0 ASC

    get search(): string {
        return this._search;
    }

    set search(v: string) {
        this._search = v;
        this.updateDropdown();
    }

    private getBarColors(): string[] {
        const selected = new Set(this.selectedNames);
        const colors: string[] = [];

        for (const a of this.visiblesData) {
            if (selected.has(a.name)) {
                colors.push('rgba(74, 222, 128, 0.4)');
            } else {
                colors.push('rgba(255, 255, 255, 0.12)');
            }
        }

        return colors;
    }

    private getBarBorderColors(): string[] {
        const selected = new Set(this.selectedNames);
        const colors: string[] = [];

        for (const a of this.visiblesData) {
            if (selected.has(a.name)) {
                colors.push('rgba(74, 222, 128, 0.8)');
            } else {
                colors.push('rgba(255, 255, 255, 0.5)');
            }
        }

        return colors;
    }

    constructor(private analysisService: AnalysisService) {
    }

    loading = true;

    ngOnInit(): void {
        this.createChart();
        this.analysisService.fetchAll().then(() => {
            this.originalData = this.analysisService.allAnalysis.filter(a => a.status !== 'Échec' && a.status !== "En cours");
            this.allTheData = this.originalData;
            this.updateDropdown();
            this.updateHisto();
            this.loading = false;
        });
    }

    ngOnChanges(changes: SimpleChanges): void {
        if (changes['selectedNames'] && this.chart) {
            this.updateHisto();
        }
    }

    ngOnDestroy(): void {
        this.chart?.destroy();
    }

    @HostListener('document:click', ['$event'])
    closeDropdown(e: MouseEvent): void {
        if (!(e.target as HTMLElement).closest('.dropdown-missions')) {
            this.dropdownOpen = false;
        }
    }

    get modeles(): string[] {
        return [...new Set(this.allTheData.map(a => a.orbital_model))];
    }

    get estimateurs(): string[] {
        return [...new Set(this.allTheData.map(a => a.estimator_type))];
    }


    sortHistogram(): void {
        const key = this.activeMetrics;

        // NO SORT → Sort DESC (operates on current allTheData, including dataset-sorted state)
        if (this.sortIcon === 'arrow-down-up') {
            this.sortIcon = 'arrow-down-1-0';
            this.tempVisible = this.allTheData;
            this.allTheData = this.visiblesData.sort((a, b) => (b[key] ?? 0) - (a[key] ?? 0));

            // Sort DESC → Sort ASC
        } else if (this.sortIcon === 'arrow-down-1-0') {
            this.sortIcon = 'arrow-up-1-0';
            this.allTheData = this.visiblesData.sort((a, b) => (a[key] ?? 0) - (b[key] ?? 0));

            // Sort ASC → NO SORT (restore pre-visible-sort state)
        } else {
            this.sortIcon = 'arrow-down-up';
            this.allTheData = this.tempVisible;
            this.tempVisible = [];
        }
        this.updateHisto();
    }

    sortDataset(): void {
        const key = this.activeMetrics;

        // Always sorts from originalData — reset visible sort since it no longer applies
        this.sortIcon = 'arrow-down-up';
        this.tempVisible = [];

        // NO SORT → Sort DESC
        if (this.dataSortIcon === 'arrow-down-up') {
            this.dataSortIcon = 'arrow-down-1-0';
            this.allTheData = [...this.originalData].sort((a, b) => (b[key] ?? 0) - (a[key] ?? 0));

            // Sort DESC → Sort ASC
        } else if (this.dataSortIcon === 'arrow-down-1-0') {
            this.dataSortIcon = 'arrow-up-1-0';
            this.allTheData = [...this.originalData].sort((a, b) => (a[key] ?? 0) - (b[key] ?? 0));

            // Sort ASC → NO SORT
        } else {
            this.dataSortIcon = 'arrow-down-up';
            this.allTheData = this.originalData;
        }
        this.updateHisto();
    }

    private updateDropdown(): void {
        const q = this._search.toLowerCase();
        this.visibleAnalysisCount = 50;

        this.filteredDatas = this.allTheData.filter(a =>
            (!q || a.name.toLowerCase().includes(q)) &&
            (!this.modelFilter || a.orbital_model === this.modelFilter) &&
            (!this.estimatorFilter || a.estimator_type === this.estimatorFilter)
        );
    }

    toggleMission(nom: string): void {
        this.selectedMission.has(nom)
            ? this.selectedMission.delete(nom)
            : this.selectedMission.add(nom);
        this.updateHisto();
    }

    highlightMissions(names: string[]): void {
        this.selectedMission.clear();
        names.forEach(n => this.selectedMission.add(n));
        this.updateDropdown();
        this.updateHisto();
    }


    toggleModelFilter(modele: string): void {
        this.modelFilter = this.modelFilter === modele ? '' : modele;
        this.updateDropdown();
        this.updateHisto();
    }

    toggleEstimatorFilter(est: string): void {
        this.estimatorFilter = this.estimatorFilter === est ? '' : est;
        this.updateDropdown();
        this.updateHisto();
    }

    selectAll(): void {
        this.filteredDatas.forEach(a => this.selectedMission.add(a.name));
        this.updateHisto();
    }

    unselectAll(): void {
        this.selectedMission.clear();
        this.updateHisto();
    }

    get allSelected(): boolean {
        return this.filteredDatas.length > 0 &&
            this.filteredDatas.every(a => this.selectedMission.has(a.name));
    }

    get visibleAnalysis(): Analyse[] {
        return this.filteredDatas.slice(0, this.visibleAnalysisCount);
    }

    get hasMoreMissions(): boolean {
        return this.filteredDatas.length > this.visibleAnalysisCount;
    }

    loadMoreMissions(): void {
        this.visibleAnalysisCount += 50;
    }

    get labelDropdown(): string {
        const n = this.selectedMission.size;
        return n === 0 ? 'Missions' : `${n} mission${n > 1 ? 's' : ''}`;
    }

    get manualSelection(): boolean {
        return this.selectedMission.size > 0;
    }


    changeMetric(key: Metric): void {
        this.sortIcon = 'arrow-down-up';
        this.activeMetrics = key;
        this.updateHisto();
    }

    changeLimit(valeur: number): void {
        this.activeLimit = valeur;
        this.customInputValue = null;
        this.selectedMission.clear();
        this.updateHisto();
    }

    applyCustom(): void {
        this.customLimitExceeded = false;

        if (!this.customInputValue || this.customInputValue <= 1) return;

        this.activeLimit = Math.min(this.customInputValue, MAX_ANALYSIS, this.allTheData.length);

        if (this.customInputValue > this.activeLimit) {
            this.customLimitExceeded = true;
            setTimeout(() => {
                this.customInputValue = this.activeLimit;
            }, 0);
        }
        this.selectedMission.clear();
        this.updateHisto();
    }

    private get visiblesData(): Analyse[] {
        if (this.selectedMission.size > 0) {
            return this.allTheData.filter(a => this.selectedMission.has(a.name));
        }
        return this.allTheData.slice(0, this.activeLimit);
    }

    private updateHisto(): void {
        const d = this.visiblesData;
        this.chart.data.labels = d.map(a => a.name);
        this.chart.data.datasets[0].data = d.map(a => a[this.activeMetrics] ?? 0);

        // get the colors
        this.chart.data.datasets[0].backgroundColor = this.getBarColors();
        this.chart.data.datasets[0].borderColor = this.getBarBorderColors();

        //(this.chart as any)._epingleIdx = null;
        //this.chart.update();
        this.chart.update();
    }

    private createChart(): void {
        const d = this.visiblesData;
        this.chart = new Chart(this.canvasRef.nativeElement, {
            type: 'bar',
            plugins: [lineHover],
            data: {
                labels: d.map(a => a.name),
                datasets: [{
                    data: d.map(a => a.rms_3d ?? 0),
                    //backgroundColor: 'rgba(255, 255, 255, 0.12)',
                    //backgroundColor: this.getBarColors(),
                    //borderColor: 'rgba(255, 255, 255, 0.5)',
                    backgroundColor: this.getBarColors(),
                    borderColor: this.getBarBorderColors(),
                    borderWidth: 1,
                    borderRadius: 4,
                    hoverBackgroundColor: 'rgba(255, 255, 255, 0.26)',
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,

                animation: {
                    duration: 150,
                },

                onHover: (_: ChartEvent, elements: ActiveElement[], chart: Chart) => {
                    (chart.canvas.style as any).cursor = elements.length ? 'crosshair' : 'default';
                },
                onClick: (_: ChartEvent, elements: ActiveElement[]) => {
                    if (!elements.length) return;
                    const idx = elements[0].index;
                    (this.chart as any)._epingleIdx = (this.chart as any)._epingleIdx === idx ? null : idx;
                    this.chart.update('none');
                },
                plugins: {
                    legend: {display: false},
                    tooltip: {callbacks: {label: ctx => " " + ctx.parsed.y + " cm"}},
                },
                scales: {
                    x: {
                        ticks: {
                            color: '#666',
                            font: {size: 11},
                            maxRotation: 0,
                            minRotation: 0,
                            callback: (value, index) => {
                                const label = (this.chart.data.labels?.[index] as string) ?? '';
                                return label.length > 12 ? label.slice(0, 12) + '…' : label;
                            },
                        },
                        grid: {color: 'rgba(255,255,255,0.04)'},
                        border: {color: '#2a2a2a'},
                    },
                    y: {
                        ticks: {color: '#666', font: {size: 11}, callback: v => `${v} cm`},
                        grid: {color: 'rgba(255,255,255,0.04)'},
                        border: {color: '#2a2a2a'},
                    },
                },
            },
        });
    }
}
