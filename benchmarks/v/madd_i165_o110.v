module madd_i165_o110 (a, b, c, r);
input [54:0] a,b,c;
output [109:0] r;

assign r = (a * b) + c;

endmodule
