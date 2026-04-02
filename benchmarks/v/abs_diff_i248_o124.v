module abs_diff_i248_o124(a,b,r);
input [123:0] a,b;
output [123:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
