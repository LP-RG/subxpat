module madd_i60_o40 (a, b, c, r);
input [19:0] a,b,c;
output [39:0] r;

assign r = (a * b) + c;

endmodule
