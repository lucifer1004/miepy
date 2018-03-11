"""
Functions related to the flux: Poynting vector, cross-sections, etc.
"""

import numpy as np
from scipy import constants
import miepy
from my_pytools.my_numpy.integrate import simps_2d

#TODO eps/mu role here (related to our definition of the H field, eps/mu factor)
def poynting_vector(E, H, eps=1, mu=1):
    """Compute the Poynting vector
    
       Arguments:
           E[3,...]   electric field data
           H[3,...]   magnetic field data
           eps        medium permitvitty (default: 1)
           mu         medium permeability (default: 1)

       Returns S[3,...]
    """

    S = 0.5*np.cross(E, np.conj(H), axis=0)
    return np.real(S)

def flux_from_poynting(E, H, Ahat, eps=1, mu=1):
    """Compute the flux from the E and H field over some area using the Poynting vector

       Arguments:
           E[3,...]             electric field values on some surface
           H[3,...]             magnetic field values on some surface
           Ahat[3,...]          normal vectors of the surface
           eps                  medium permitvitty (default: 1)
           mu                   medium permeability (default: 1)

       Returns flux (scalar)
    """
    S = poynting_vector(E, H, eps, mu)
    integrand = np.einsum('i...,i...->...', S, Ahat)

    return np.sum(integrand)

def flux_from_poynting_sphere(E, H, radius, eps=1, mu=1):
    """Compute the flux from the E and H field on the surface of a sphere using the Poynting vector

       Arguments:
           E[3,Ntheta,Nphi]     electric field values on the surface of a sphere
           H[3,Ntheta,Nphi]     magnetic field values on the surface of a sphere
           radius               radius of sphere 
           eps                  medium permitvitty (default: 1)
           mu                   medium permeability (default: 1)

       Returns flux (scalar)
    """
    S = poynting_vector(E, H, eps, mu)

    Ntheta, Nphi = E.shape[1:]
    THETA, PHI = miepy.coordinates.sphere_mesh(Ntheta)
    rhat,*_ = miepy.coordinates.sph_basis_vectors(THETA, PHI)

    tau = np.linspace(-1, 1, Ntheta)
    phi = np.linspace(0, 2*np.pi, Nphi)
    dA = radius**2

    integrand = np.einsum('ixy,ixy->xy', S, rhat)*dA
    flux = simps_2d(tau, phi, integrand)

    return flux

def _gmt_flux_from_poynting(gmt, i, sampling=30):
    """FOR TESTING ONLY!
    Given GMT object and particle number i, return flux from poynting vector
    """
    radius = gmt.spheres.radius[i]
    X,Y,Z,THETA,PHI,tau,phi = miepy.coordinates.cart_sphere_mesh(radius, gmt.spheres.position[i], sampling)

    E = gmt.E_field_from_particle(i, X, Y, Z)
    H = gmt.H_field_from_particle(i, X, Y, Z)

    flux = np.zeros(gmt.Nfreq)

    for k in range(gmt.Nfreq):
        eps_b = gmt.material_data['eps_b'][k]
        mu_b = gmt.material_data['mu_b'][k]
        flux[k] = flux_from_poynting_sphere(E[:,k], H[:,k], radius, eps_b, mu_b)

    return F,T
