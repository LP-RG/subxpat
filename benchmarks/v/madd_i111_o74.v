module madd_i111_o74 (a, b, c, r);
input [36:0] a,b,c;
output [73:0] r;

assign r = (a * b) + c;

endmodule
