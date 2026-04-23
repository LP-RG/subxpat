module mul_i512_o512 (a, b, r);
input [255:0] a,b;
output [511:0] r;

assign r = a * b;

endmodule
