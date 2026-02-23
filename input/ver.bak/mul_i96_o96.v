module mul_i96_o96 (a, b, r);
input [47:0] a,b;
output [95:0] r;

assign r = a * b;

endmodule
