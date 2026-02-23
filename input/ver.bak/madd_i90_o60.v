module madd_i90_o60 (a, b, c, r);
input [29:0] a,b,c;
output [59:0] r;

assign r = (a * b) + c;

endmodule
