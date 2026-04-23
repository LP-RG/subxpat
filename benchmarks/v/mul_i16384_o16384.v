module mul_i16384_o16384 (a, b, r);
input [8191:0] a,b;
output [16383:0] r;

assign r = a * b;

endmodule
