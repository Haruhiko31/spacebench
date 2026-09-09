import {Component, EventEmitter, Output} from '@angular/core';
import {CommonModule} from '@angular/common';
import {Dialog} from "primeng/dialog";

interface ErrorCode {
    code: string;
    cause: string;
    action: string;
}

interface ErrorSection {
    title: string;
    errors: ErrorCode[];
}

@Component({
    selector: 'app-file-formats',
    standalone: true,
    imports: [CommonModule, Dialog],
    templateUrl: './file-formats.component.html',
    styleUrls: ['./file-formats.component.scss'],
})
export class FileFormatsComponent {
    @Output() close = new EventEmitter<void>();

    exampleVisible = false;
    fileType = '';
    imgSrc = '';

    rsoSp3Tab: 'P' | 'V' = 'P';
    igsSp3Tab: 'P' | 'V' = 'P';

    showExample(fileType: string) {
        this.exampleVisible = !this.exampleVisible
        this.fileType = fileType;
        this.imgSrc = '/assets/img/pod/' + fileType + '.svg';
    }

    closeExample() {
        this.exampleVisible = false;
        this.fileType = '';
        this.imgSrc = '';
    }


    // ═══════ VALIDATION ERROR CODES ══════════════════════════════════

    errorCodeVisible = false;
    errorCodeTitle = '';
    errorSections: ErrorSection[] = [];

    private allErrors: Record<string, ErrorSection[]> = {
        'SP3': [
            {
                title: 'Erreurs communes',
                errors: [
                    {
                        code: 'FILE_EMPTY',
                        cause: 'Le fichier est vide.',
                        action: 'Vérifier que le fichier contient des données.'
                    },
                    {
                        code: 'COMMON_FILE_DECODE_ERROR',
                        cause: 'Le fichier ne peut pas être décodé (ASCII attendu).',
                        action: 'Vérifier l\'encodage ou régénérer le fichier.'
                    },
                ]
            },
            {
                title: 'Erreurs SP3',
                errors: [
                    {
                        code: 'SP3_FILE_TOO_SHORT',
                        cause: 'Trop peu de lignes pour un SP3 valide.',
                        action: 'Vérifier que le fichier n\'est pas tronqué.'
                    },
                    {
                        code: 'SP3_FILE_HEADER_ERROR',
                        cause: 'Première ligne d\'en-tête incomplète ou mal formée.',
                        action: 'Vérifier la première ligne (#dP… ou #dV…).'
                    },
                    {
                        code: 'SP3_FILE_VERSION_ERROR',
                        cause: 'Version SP3 non reconnue.',
                        action: 'Versions acceptées : #a, #b, #c, #d.'
                    },
                    {
                        code: 'SP3_FILE_MODE_ERROR',
                        cause: 'Mode SP3 invalide ou incohérent avec le contenu.',
                        action: 'Vérifier le caractère P ou V en première ligne.'
                    },
                    {
                        code: 'SP3_FILE_START_EPOCH_ERROR',
                        cause: 'Époque de départ illisible dans l\'en-tête.',
                        action: 'Vérifier les champs date/heure.'
                    },
                    {
                        code: 'SP3_FILE_EPOCH_COUNT_ERROR',
                        cause: 'Nombre d\'époques absent, invalide ou nul.',
                        action: 'Vérifier le champ nombre d\'époques.'
                    },
                    {
                        code: 'SP3_FILE_NUMBER_OF_SATS_ERROR',
                        cause: 'Aucun satellite dans les lignes + de l\'en-tête.',
                        action: 'Vérifier la liste des satellites.'
                    },
                    {
                        code: 'SP3_FILE_FIRST_EPOCH_ERROR',
                        cause: 'Aucune première époque valide trouvée.',
                        action: 'Vérifier les lignes commençant par *.'
                    },
                    {
                        code: 'SP3_FILE_DATA_ERROR',
                        cause: 'Une époque existe mais aucune donnée ne suit.',
                        action: 'Vérifier les lignes P… ou V… après les époques.'
                    },
                    {
                        code: 'SP3_FILE_MISSING_POSITION_ERROR',
                        cause: 'Aucun enregistrement P trouvé.',
                        action: 'Vérifier les lignes de position.'
                    },
                    {
                        code: 'SP3_FILE_MISSING_VELOCITY_ERROR',
                        cause: 'Mode V déclaré mais aucune ligne V trouvée.',
                        action: 'Vérifier les lignes de vitesse.'
                    },
                    {
                        code: 'SP3_FILE_EOF_ERROR',
                        cause: 'Le fichier ne se termine pas par EOF.',
                        action: 'Vérifier que le fichier n\'est pas tronqué.'
                    },
                    {
                        code: 'SP3_FILE_EPOCH_ERROR',
                        cause: 'Première époque incohérente avec l\'en-tête.',
                        action: 'Vérifier la cohérence temporelle.'
                    },
                ]
            }
        ],
        'CLK 30S': [
            {
                title: 'Erreurs communes',
                errors: [
                    {
                        code: 'FILE_EMPTY',
                        cause: 'Le fichier est vide.',
                        action: 'Vérifier que le fichier contient des données.'
                    },
                    {
                        code: 'COMMON_FILE_DECODE_ERROR',
                        cause: 'Le fichier ne peut pas être décodé (ASCII attendu).',
                        action: 'Vérifier l\'encodage ou régénérer le fichier.'
                    },
                ]
            },
            {
                title: 'Erreurs CLK',
                errors: [
                    {
                        code: 'CLK_FILE_HEADER_ERROR',
                        cause: 'En-tête CLK absent ou incomplet.',
                        action: 'Vérifier que l\'en-tête se termine par END OF HEADER.'
                    },
                    {
                        code: 'CLK_FILE_VERSION_ERROR',
                        cause: 'Version RINEX Clock invalide ou non supportée.',
                        action: 'Fournir un fichier CLK RINEX 3.'
                    },
                    {
                        code: 'CLK_FILE_TYPE_ERROR',
                        cause: 'Le type n\'est pas C.',
                        action: 'Vérifier que c\'est un fichier d\'horloges.'
                    },
                    {
                        code: 'CLK_FILE_DATA_ERROR',
                        cause: 'Aucun enregistrement AS trouvé.',
                        action: 'Fournir un fichier avec des horloges satellites AS.'
                    },
                    {
                        code: 'CLK_FILE_TIMESTAMP_ERROR',
                        cause: 'Timestamp du premier AS invalide.',
                        action: 'Vérifier la première ligne AS.'
                    },
                ]
            }
        ],
        'RINEX': [
            {
                title: 'Erreurs communes',
                errors: [
                    {
                        code: 'FILE_EMPTY',
                        cause: 'Le fichier est vide.',
                        action: 'Vérifier que le fichier contient des données.'
                    },
                    {
                        code: 'COMMON_FILE_DECODE_ERROR',
                        cause: 'Le fichier ne peut pas être décodé (ASCII attendu).',
                        action: 'Vérifier l\'encodage ou régénérer le fichier.'
                    },
                ]
            },
            {
                title: 'Erreurs RINEX Observation',
                errors: [
                    {
                        code: 'RINEX_FILE_TOO_SHORT',
                        cause: 'Le fichier est trop court pour être un RINEX valide.',
                        action: 'Vérifier que le fichier n\'est pas tronqué.'
                    },
                    {
                        code: 'RINEX_FILE_HEADER_ERROR',
                        cause: 'Ligne RINEX VERSION / TYPE absente ou en-tête incomplet.',
                        action: 'Vérifier que l\'en-tête contient END OF HEADER.'
                    },
                    {
                        code: 'RINEX_FILE_VERSION_ERROR',
                        cause: 'Version RINEX absente, invalide ou non supportée.',
                        action: 'Fournir un fichier d\'observations RINEX 2.'
                    },
                    {
                        code: 'RINEX_FILE_TYPE_ERROR',
                        cause: 'Le fichier n\'est pas déclaré comme OBSERVATION DATA.',
                        action: 'Vérifier que c\'est un fichier d\'observations.'
                    },
                    {
                        code: 'RINEX_FILE_OBSERVATION_TYPE_ERROR',
                        cause: 'La ligne # / TYPES OF OBSERV est absente.',
                        action: 'Vérifier que l\'en-tête déclare les types d\'observation.'
                    },
                    {
                        code: 'RINEX_FILE_OBSERVATION_COUNT_ERROR',
                        cause: 'Nombre de types d\'observation absent, invalide ou nul.',
                        action: 'Vérifier la ligne # / TYPES OF OBSERV (ex: 9 L1 L2 C1…).'
                    },
                    {
                        code: 'RINEX_FILE_START_EPOCH_ERROR',
                        cause: 'Ligne TIME OF FIRST OBS absente ou invalide.',
                        action: 'Vérifier la date de première observation dans l\'en-tête.'
                    },
                    {
                        code: 'RINEX_FILE_FIRST_EPOCH_ERROR',
                        cause: 'Aucune première époque d\'observation trouvée après l\'en-tête.',
                        action: 'Vérifier les données après END OF HEADER.'
                    },
                    {
                        code: 'RINEX_FILE_EPOCH_ERROR',
                        cause: 'Première époque incohérente avec TIME OF FIRST OBS.',
                        action: 'Vérifier la cohérence temporelle entre en-tête et données.'
                    },
                    {
                        code: 'RINEX_FILE_EPOCH_FLAG_ERROR',
                        cause: 'Marqueur de la première époque invalide ou non supporté.',
                        action: 'Vérifier le champ epoch flag (valeurs normales : 0 ou 1).'
                    },
                    {
                        code: 'RINEX_FILE_START_EPOCH_SAT_COUNT_ERROR',
                        cause: 'Nombre de satellites dans la première époque absent, invalide ou nul.',
                        action: 'Vérifier la ligne de première époque.'
                    },
                    {
                        code: 'RINEX_FILE_FIRST_DATA_ERROR',
                        cause: 'Données d\'observation après la première époque absentes ou incomplètes.',
                        action: 'Vérifier les blocs d\'observations par satellite.'
                    },
                ]
            }
        ],
        'PYTHON': [
            {
                title: 'Erreurs communes',
                errors: [
                    {
                        code: 'FILE_EMPTY',
                        cause: 'Le fichier est vide.',
                        action: 'Vérifier que le fichier contient des données.'
                    },
                    {
                        code: 'COMMON_FILE_DECODE_ERROR',
                        cause: 'Le fichier ne peut pas être décodé (UTF-8 attendu).',
                        action: 'Vérifier l\'encodage ou régénérer le fichier.'
                    },
                ]
            },
            {
                title: 'Erreurs plugin Python',
                errors: [
                    {
                        code: 'PY_FILE_SYNTAX_ERROR',
                        cause: 'Le fichier Python contient une erreur de syntaxe.',
                        action: 'Corriger la syntaxe du fichier .py.'
                    },
                    {
                        code: 'PY_FILE_CUSTOM_ESTIMATOR_ERROR',
                        cause: 'Aucune classe CustomEstimator trouvée.',
                        action: 'Définir une classe nommée exactement CustomEstimator.'
                    },
                    {
                        code: 'PY_FILE_BASE_ESTIMATOR_ERROR',
                        cause: 'CustomEstimator n\'hérite pas de BaseEstimator.',
                        action: 'Déclarer class CustomEstimator(BaseEstimator):.'
                    },
                    {
                        code: 'PY_FILE_ESTIMATE_METHOD_ERROR',
                        cause: 'La méthode estimate est absente.',
                        action: 'Ajouter une méthode estimate(...) dans CustomEstimator.'
                    },
                    {
                        code: 'PY_FILE_FORBIDDEN_IMPORT',
                        cause: 'Import d\'un module interdit (os, sys, subprocess, socket…).',
                        action: 'Supprimer les imports dangereux.'
                    },
                    {
                        code: 'PY_FILE_FORBIDDEN_CALL',
                        cause: 'Appel d\'une fonction interdite (eval, exec, compile, __import__, open, input…).',
                        action: 'Supprimer les appels dangereux.'
                    },
                ]
            }
        ]
    };

    showErrorCode(fileType: string) {
        this.errorCodeTitle = fileType;
        this.errorSections = this.allErrors[fileType] ?? [];
        this.errorCodeVisible = true;
    }


    closeErrorCode() {
        this.errorCodeVisible = false;
    }


}
