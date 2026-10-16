clear, clc
Ts = 1/(48e3);
f = 60;
Vg = 110;
Vcc = 350;
Rs = 0.1;
R = 0.1;
Ls = 10e-3;
C = 1000e-6;

A = (2/3)*[1 -1/2 -1/2; 0 sqrt(3)/2 -sqrt(3)/2];

%THD = power_fftscope(out.Iabc);