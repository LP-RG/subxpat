module madd_i120_o80 (a, b, c, r);
input [39:0] a,b,c;
output [79:0] r;

assign r = (a * b) + c;

endmodule
