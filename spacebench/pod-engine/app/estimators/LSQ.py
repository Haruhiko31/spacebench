import numpy as np
from .base import BaseEstimator

C = 299792458  # speed of light

class LSQEstimator(BaseEstimator):

    def estimate_epoch(self, epoch_obs, initial_state) -> tuple[np.ndarray, dict]:

        max_iter = self.config.max_iteration
        tolerance = self.config.tolerance

        state = np.asarray(initial_state, dtype=float).copy()

        iter_to_stop = 0
        corrections_history = []

        for iteration in range(max_iter):

            receiver_pos = state[0:3]  # init_state[x,y,z]
            receiver_clock_bias = state[3]  # init_state clock bias

            jacobian_rows = []
            residuals = []

            # foreach satellites
            for sv in epoch_obs:
                P_observed = epoch_obs[sv]['P']  # observed pseudorange
                sat_pos = epoch_obs[sv]['sat_pos']  # GNSS Sat pos [m]
                dt_sat = epoch_obs[sv]['dt_sat']  # satellite clock bias [s]

                # get p^j (rho) from deltaX, deltaY, deltaZ

                dx = receiver_pos[0] - sat_pos[0]
                dy = receiver_pos[1] - sat_pos[1]
                dz = receiver_pos[2] - sat_pos[2]

                rho = np.sqrt(dx ** 2 + dy ** 2 + dz ** 2)

                if rho == 0:
                    continue

                P_computed = rho + receiver_clock_bias - C * dt_sat

                residual_row = P_observed - P_computed

                jacobian_matrix = np.array([
                    dx / rho,  # X
                    dy / rho,  # Y
                    dz / rho,  # Z
                    1.0
                ])

                jacobian_rows.append(jacobian_matrix)
                residuals.append(residual_row)

            if len(jacobian_rows) < 4:
                raise ValueError("At least 4 sats are needed for LSQ Estimation")

            H = np.vstack(jacobian_rows)
            residual_vector = np.asarray(residuals, dtype=float)

            correction, residuals, rank, singular_values = np.linalg.lstsq(H, residual_vector, rcond=None)

            state = state + correction

            position_correction_norm = np.sqrt(
                correction[0] ** 2 +
                correction[1] ** 2 +
                correction[2] ** 2
            )  # sqrt(dx²+dy²+dz²)

            corrections_history.append(position_correction_norm)

            DEBUG_LSQ = False

            if DEBUG_LSQ:
                print(f"Iteration {iteration}")
                print(f"Correction: {correction}")
                print(f"Position correction norm: {position_correction_norm}")
                print(f"Rank: {rank}")

            if position_correction_norm < tolerance:
                iter_to_stop = iteration + 1
                break

        return state, {
            "iterations_to_stop": iter_to_stop,
            "corrections_history": corrections_history
        }




# Equation based on Code Base Positioning (https://gssc.esa.int/navipedia/index.php/Code_Based_Positioning_%28SPS%29)

# The target is to estimate the sat pos as r = (x,y,z) and the receiver clock bias delta_t_rcv.

''' R^j = p^j + c * (\delta(j) - \delta(t^j)) + T^j + alpha*I^j + TGD^j + M^j + vareps^j
R^j = Observed Pseudorange for satellite        → (P)
p^j = geometric distance between receiver       → (receiver_pos - sat_pos)
c = speed of light                              → 299792458m/s       
\delta(t) = receiver clock bias                 → to estimate
\delta(t^j) = satellite clock bias) → (dt)      → dt_sat
T^j = tropospheric delay                        → will ignore for MVP
alpha*I^j = ionospheric delay                   → will ignore for MVP
TGD^j = Satellite group delay                   → will ignore for MVP
M^j = multipath                                 → will ignore for MVP
vareps^j = measurement noise / residual


:: becomes ::

R^j = rho^j + c(delta_t_rcv - delta_t_sat^j) + eps^j
R^j = rho^j + b - c * delta_t_sat^j + eps^j

'''
'''
What we want (simplified for this MVP...)
R^j = rho^j + c(delta_t_rcv - delta_t_sat^j) + eps^j

p_j (rho) could be rewritten also as sqrt( (x^sat - x^rcv)² + (y^sat - y^rcv)² + (z^sat - z^rcv)² ) (written dx, dy, dz)

b = c * delta_t_rcv (bias)
b = receiver_block_bias

final equ : R^j = sqrt( dx² + dy² + dz²) + b - c * delta_t_sat^j +  residual

'''

'''
Navipedia — Code Based Positioning : pour comprendre Rj, Pj, deltaT et le besoin d’au moins quatre satellites.
Navipedia — Geometric Range Modelling : pour justifier la racine carrée / distance euclidienne.
Montenbruck & Gill, section 8.1.1 : pour expliquer z=h(x)+ε, linéarisation, Jacobienne, correction itérative.
NumPy linalg.lstsq documentation : pour justifier le solveur utilisé.
NumPy linalg.norm documentation uniquement si tu utilises np.linalg.norm. Si tu gardes np.sqrt(dx**2+dy**2+dz**2), tu n’as même pas besoin de t’appuyer dessus fortement.

'''
