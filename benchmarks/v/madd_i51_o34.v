module madd_i51_o34 (a, b, c, r);
input [16:0] a,b,c;
output [33:0] r;

assign r = (a * b) + c;

endmodule
