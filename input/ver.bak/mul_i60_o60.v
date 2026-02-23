module mul_i60_o60 (a, b, r);
input [29:0] a,b;
output [59:0] r;

assign r = a * b;

endmodule
