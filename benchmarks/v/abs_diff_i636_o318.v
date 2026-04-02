module abs_diff_i636_o318(a,b,r);
input [317:0] a,b;
output [317:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
