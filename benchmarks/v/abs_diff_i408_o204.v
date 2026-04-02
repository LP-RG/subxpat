module abs_diff_i408_o204(a,b,r);
input [203:0] a,b;
output [203:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
