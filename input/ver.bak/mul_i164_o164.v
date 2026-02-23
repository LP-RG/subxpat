module mul_i164_o164 (a, b, r);
input [81:0] a,b;
output [163:0] r;

assign r = a * b;

endmodule
