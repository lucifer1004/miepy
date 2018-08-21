"""
Expressions for the force and torque given the expansion coefficients or the fields
"""

import numpy as np
from scipy import constants
import miepy
from miepy.vsh.misc import simps_2d
from miepy.cpp.special import force

def levi_civita():
    """return the levi-civita symbol"""

    eijk = np.zeros((3, 3, 3))
    eijk[0, 1, 2] = eijk[1, 2, 0] = eijk[2, 0, 1] = 1
    eijk[0, 2, 1] = eijk[2, 1, 0] = eijk[1, 0, 2] = -1
    return eijk

def torque(p_scat, p_inc, k, eps_b, mu_b):
    """torque from the expansion coefficients
    
       Arguments:
           p_scat[2,rmax]   scattering coefficients
           p_inc[2,rmax]    incident coefficients
           k        wavenumber
           eps_b    background relative permitvitty
           mu_b     background relative permeability
    """
    T = np.zeros(3, dtype=float)
    A = -2*np.pi/k**3*constants.epsilon_0*eps_b**0.5

    lmax = miepy.vsh.rmax_to_lmax(p_scat.shape[1])

    p, q = p_scat
    p_inc, q_inc = p_inc
    for r,n,m in miepy.mode_indices(lmax):
        if m != n:
            # Tx
            factor = -A*np.sqrt((n-m)*(n+m+1))
            r1 = n**2 + n - 1 + m + 1
            T[0] += factor*np.real(p[r]*np.conj(p[r1]) \
                    + q[r]*np.conj(q[r1]) \
                    -0.5*(p[r1]*np.conj(p_inc[r]) \
                    + p[r]*np.conj(p_inc[r1]) \
                    + q[r1]*np.conj(q_inc[r]) \
                    + q[r]*np.conj(q_inc[r1])))

            # Ty
            T[1] += factor*np.imag(p[r]*np.conj(p[r1]) \
                    + q[r]*np.conj(q[r1]) \
                    +0.5*(p[r1]*np.conj(p_inc[r]) \
                    - p[r]*np.conj(p_inc[r1]) \
                    + q[r1]*np.conj(q_inc[r]) \
                    - q[r]*np.conj(q_inc[r1])))

        # Tz
        factor = A*m
        T[2] += factor* (np.abs(p[r])**2 + np.abs(q[r])**2 \
                - np.real(p[r]*np.conj(p_inc[r]) \
                + q[r]*np.conj(q_inc[r])))

    return T

def maxwell_stress_tensor(E, H, eps=1, mu=1):
    """Compute the Maxwell stress tensor
    
       Arguments:
           E[3,...]   electric field data
           H[3,...]   magnetic field data
           eps        medium permitvitty (default: 1)
           mu         medium permeability (default: 1)

       Returns T[3,3,...]
    """
    sigma = eps*np.einsum('i...,j...->ij...', E, np.conj(E)) \
            + mu*np.einsum('i...,j...->ij...', H, np.conj(H)) \
            - 0.5*np.einsum('ij,...->ij...', np.identity(3), eps*np.sum(np.abs(E)**2, axis=0)) \
            - 0.5*np.einsum('ij,...->ij...', np.identity(3), mu*np.sum(np.abs(H)**2, axis=0))
    sigma *= constants.epsilon_0/2

    return sigma

def force_and_torque_from_mst(E, H, radius, eps=1, mu=1):
    """Compute the force and torque on a particle using the Maxwell stress tensor

       Arguments:
           E[3,Ntheta,Nphi]     electric field values on the surface of a sphere
           H[3,Ntheta,Nphi]     magnetic field values on the surface of a sphere
           radius               radius of sphere 
           eps                  medium permitvitty (default: 1)
           mu                   medium permeability (default: 1)

       Returns (F[3], T[3])
    """
    sigma = maxwell_stress_tensor(E, H, eps, mu)
    levi = levi_civita()
    dA = radius**2

    Ntheta, Nphi = E.shape[1:]
    THETA, PHI = miepy.coordinates.sphere_mesh(Ntheta)
    rhat,*_ = miepy.coordinates.sph_basis_vectors(THETA, PHI)

    tau = np.linspace(-1, 1, Ntheta)
    phi = np.linspace(0, 2*np.pi, Nphi)

    integrand = np.einsum('ijxy,jxy->ixy', sigma, rhat)*dA
    F = np.array([simps_2d(tau, phi, integrand[x].real) for x in range(3)])

    integrand = np.einsum('imn,mxy,njxy,jxy->ixy', levi, radius*rhat, sigma, rhat)*dA
    T = np.array([simps_2d(tau, phi, integrand[x].real) for x in range(3)])

    return F,T

def _gmt_force_and_torque_from_mst(gmt, i, sampling=30):
    """FOR TESTING ONLY!
    Given GMT object and particle number i, return F,T using MST
    """
    radius = gmt.radius[i]
    X,Y,Z,THETA,PHI,tau,phi = miepy.coordinates.cart_sphere_mesh(radius, gmt.position[i], sampling)

    E = gmt.E_field_from_particle(i, X, Y, Z)
    H = gmt.H_field_from_particle(i, X, Y, Z)

    eps_b = gmt.material_data.eps_b
    mu_b = gmt.material_data.mu_b
    F, T = force_and_torque_from_mst(E, H, radius, eps_b, mu_b)

    return F,T
