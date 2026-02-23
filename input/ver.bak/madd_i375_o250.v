module madd_i375_o250 (a, b, c, r);
input [124:0] a,b,c;
output [249:0] r;

assign r = (a * b) + c;

endmodule
