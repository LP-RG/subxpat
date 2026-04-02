module madd_i279_o186 (a, b, c, r);
input [92:0] a,b,c;
output [185:0] r;

assign r = (a * b) + c;

endmodule
