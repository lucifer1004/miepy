"""
functions for building interaction matrices and solving them
"""

import numpy as np
import miepy

#TODO vectorize for loops. Avoid transpose of position->pass x,y,z to source instead...?
def sphere_cluster_tmatrix(positions, a, k):
    """Obtain the T-matrix for a cluster of spheres.
       Returns T[2,N,rmax,2,N,rmax]
    
       Arguments:
           positions[N,3]      particles positions
           a[N,2,lmax]         mie scattering coefficients
           k                   medium wavenumber
    """
    Nparticles = positions.shape[0]
    lmax = a.shape[-1]
    rmax = miepy.vsh.lmax_to_rmax(lmax)
    identity = np.zeros(shape = (Nparticles, 2, rmax, Nparticles, 2, rmax), dtype=complex)
    np.einsum('airair->air', identity)[...] = 1
    
    interaction_matrix = np.zeros(shape = (Nparticles, 2, rmax, Nparticles, 2, rmax), dtype=complex)

    for i in range(Nparticles):
        for j in range(i+1, Nparticles):
            pi = positions[i]
            pj = positions[j]
            dji = pi -  pj
            r_ji = np.linalg.norm(dji)
            theta_ji = np.arccos(dji[2]/r_ji)
            phi_ji = np.arctan2(dji[1], dji[0])

            for r,n,m in miepy.mode_indices(lmax):
                for s,v,u in miepy.mode_indices(lmax):
                    if s - 2*u < r: continue

                    A_transfer, B_transfer = miepy.vsh.vsh_translation(m, n, u, v, 
                            r_ji, theta_ji, phi_ji, k, miepy.VSH_mode.outgoing)

                    interaction_matrix[i,0,r,j,0,s] = A_transfer*a[j,0,v-1]
                    interaction_matrix[i,0,r,j,1,s] = B_transfer*a[j,1,v-1]
                    interaction_matrix[i,1,r,j,0,s] = B_transfer*a[j,0,v-1]
                    interaction_matrix[i,1,r,j,1,s] = A_transfer*a[j,1,v-1]

                    interaction_matrix[j,0,r,i,0,s] = (-1)**(n+v)*A_transfer*a[i,0,v-1]
                    interaction_matrix[j,0,r,i,1,s] = (-1)**(n+v+1)*B_transfer*a[i,1,v-1]
                    interaction_matrix[j,1,r,i,0,s] = (-1)**(n+v+1)*B_transfer*a[i,0,v-1]
                    interaction_matrix[j,1,r,i,1,s] = (-1)**(n+v)*A_transfer*a[i,1,v-1]

                    interaction_matrix[i,0,s-2*u,j,0,r-2*m] = (-1)**(m+u)*A_transfer*a[j,0,n-1]
                    interaction_matrix[i,0,s-2*u,j,1,r-2*m] = (-1)**(m+u+1)*B_transfer*a[j,1,n-1]
                    interaction_matrix[i,1,s-2*u,j,0,r-2*m] = (-1)**(m+u+1)*B_transfer*a[j,0,n-1]
                    interaction_matrix[i,1,s-2*u,j,1,r-2*m] = (-1)**(m+u)*A_transfer*a[j,1,n-1]

                    interaction_matrix[j,0,s-2*u,i,0,r-2*m] = (-1)**(m+u+n+v)*A_transfer*a[i,0,n-1]
                    interaction_matrix[j,0,s-2*u,i,1,r-2*m] = (-1)**(m+u+n+v)*B_transfer*a[i,1,n-1]
                    interaction_matrix[j,1,s-2*u,i,0,r-2*m] = (-1)**(m+u+n+v)*B_transfer*a[i,0,n-1]
                    interaction_matrix[j,1,s-2*u,i,1,r-2*m] = (-1)**(m+u+n+v)*A_transfer*a[i,1,n-1]

    t_matrix = identity + interaction_matrix
    return t_matrix

def solve_sphere_cluster(positions, a, p_src, k):
    """Solve interactions of a collection of spheres.
       Returns [p_inc, q_inc]
    
       Arguments:
           positions[N,3]      particles positions
           a[N,2,lmax]         mie scattering coefficients
           p_src[N,2,rmax]     source scattering coefficients
           k                   medium wavenumber
    """
    A = sphere_cluster_tmatrix(positions, a,  k)
    sol = np.linalg.tensorsolve(A, p_src)

    return sol

#TODO vectorize for loops. Avoid transpose of position->pass x,y,z to source instead...?
#TODO this function is more general than above and can be used for both cases (change only the einsum)
def particle_cluster_tmatrix(positions, tmatrix, k):
    """Obtain the T-matrix for a cluster of particles.
       Returns T[2,N,rmax,2,N,rmax]
    
       Arguments:
           positions[N,3]      particles positions
           tmatrix[N,2,rmax,2,rmax]   particle T-matrices
           k                   medium wavenumber
    """
    Nparticles = positions.shape[0]
    rmax = tmatrix.shape[-1]
    lmax = miepy.vsh.rmax_to_lmax(rmax)
    identity = np.zeros(shape = (Nparticles, 2, rmax, Nparticles, 2, rmax), dtype=complex)
    np.einsum('airair->air', identity)[...] = 1
    
    interaction_matrix = np.zeros(shape = (Nparticles, 2, rmax, Nparticles, 2, rmax), dtype=complex)

    for i in range(Nparticles):
        for j in range(i+1, Nparticles):
            pi = positions[i]
            pj = positions[j]
            dji = pi -  pj
            r_ji = np.linalg.norm(dji)
            theta_ji = np.arccos(dji[2]/r_ji)
            phi_ji = np.arctan2(dji[1], dji[0])

            for r,n,m in miepy.mode_indices(lmax):
                for s,v,u in miepy.mode_indices(lmax):
                    if s - 2*u < r: continue

                    A_transfer, B_transfer = miepy.vsh.vsh_translation(m, n, u, v, 
                            r_ji, theta_ji, phi_ji, k, miepy.VSH_mode.outgoing)

                    interaction_matrix[i,0,r,j,0,s] = A_transfer
                    interaction_matrix[i,0,r,j,1,s] = B_transfer
                    interaction_matrix[i,1,r,j,0,s] = B_transfer
                    interaction_matrix[i,1,r,j,1,s] = A_transfer

                    interaction_matrix[j,0,r,i,0,s] = (-1)**(n+v)*A_transfer
                    interaction_matrix[j,0,r,i,1,s] = (-1)**(n+v+1)*B_transfer
                    interaction_matrix[j,1,r,i,0,s] = (-1)**(n+v+1)*B_transfer
                    interaction_matrix[j,1,r,i,1,s] = (-1)**(n+v)*A_transfer

                    interaction_matrix[i,0,s-2*u,j,0,r-2*m] = (-1)**(m+u)*A_transfer
                    interaction_matrix[i,0,s-2*u,j,1,r-2*m] = (-1)**(m+u+1)*B_transfer
                    interaction_matrix[i,1,s-2*u,j,0,r-2*m] = (-1)**(m+u+1)*B_transfer
                    interaction_matrix[i,1,s-2*u,j,1,r-2*m] = (-1)**(m+u)*A_transfer

                    interaction_matrix[j,0,s-2*u,i,0,r-2*m] = (-1)**(m+u+n+v)*A_transfer
                    interaction_matrix[j,0,s-2*u,i,1,r-2*m] = (-1)**(m+u+n+v)*B_transfer
                    interaction_matrix[j,1,s-2*u,i,0,r-2*m] = (-1)**(m+u+n+v)*B_transfer
                    interaction_matrix[j,1,s-2*u,i,1,r-2*m] = (-1)**(m+u+n+v)*A_transfer

    interaction_matrix = np.einsum('iabjcd,jcdef->iabjef', interaction_matrix, tmatrix)
    A = identity + interaction_matrix
    return A

def solve_particle_cluster(positions, tmatrix, p_src, k):
    """Solve interactions of a collection of particles
       Returns [p_inc, q_inc]
    
       Arguments:
           positions[N,3]      particles positions
           tmatrix[N,2,rmax,2,rmax]   particle T-matrices
           p_src[N,2,rmax]     source scattering coefficients
           k                   medium wavenumber
    """
    A = particle_cluster_tmatrix(positions, tmatrix,  k)
    sol = np.linalg.tensorsolve(A, p_src)

    return sol

